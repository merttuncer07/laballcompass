import unittest

import numpy as np

from corma import audit_state_space


class CORMATests(unittest.TestCase):
    def test_full_minimal_system(self) -> None:
        result = audit_state_space([[0.7, 0.0], [0.0, 0.4]], [[1.0], [1.0]], [[1.0, 1.0]])
        self.assertEqual(result.status, "MINIMAL_REALIZATION")
        self.assertEqual(result.minimal_io_dimension, 2)

    def test_four_kalman_categories_are_exposed(self) -> None:
        result = audit_state_space(
            np.diag([0.8, 0.6, 0.5, 0.3]),
            [[1.0], [0.0], [1.0], [0.0]],
            [[1.0, 1.0, 0.0, 0.0]],
            horizon=8,
        )
        self.assertEqual(
            (result.controllable_observable, result.controllable_unobservable,
             result.uncontrollable_observable, result.uncontrollable_unobservable),
            (1, 1, 1, 1),
        )
        self.assertEqual(result.redundant_state_count, 3)

    def test_no_io_channel_is_detected(self) -> None:
        result = audit_state_space([[0.5]], [[1.0]], [[0.0]])
        self.assertEqual(result.status, "NO_INPUT_OUTPUT_DYNAMIC_CHANNEL")
        self.assertEqual(result.minimal_io_dimension, 0)

    def test_bad_shapes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            audit_state_space([[1.0, 0.0]], [[1.0]], [[1.0]])


if __name__ == "__main__":
    unittest.main()
