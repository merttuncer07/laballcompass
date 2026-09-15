from __future__ import annotations

import unittest

from twmr import TargetWeightedModelReducer


class TargetWeightedModelReducerTests(unittest.TestCase):
    def test_target_reducer_retains_output_relevant_state(self) -> None:
        reducer = TargetWeightedModelReducer(
            [[0.9, 0], [0, 0.8]], [[10], [1]], [[0, 5]], ["energy", "target"]
        )
        result = reducer.reduce(1, 10)
        self.assertEqual(result.retained_states, ("target",))

    def test_full_retention_has_zero_error(self) -> None:
        reducer = TargetWeightedModelReducer([[0.5]], [[1]], [[1]])
        result = reducer.reduce(1, 5)
        self.assertAlmostEqual(result.target_impulse_error, 0.0)

    def test_invalid_dimension_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TargetWeightedModelReducer([[1, 0], [0, 1]], [[1]], [[1, 0]])


if __name__ == "__main__":
    unittest.main()
