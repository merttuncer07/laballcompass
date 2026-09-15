import unittest

import numpy as np

from bred import design_balanced_reduction


class BREDTests(unittest.TestCase):
    def test_small_channel_is_removed_within_budget(self) -> None:
        result = design_balanced_reduction(
            np.diag([0.8, 0.2]), np.diag([1.0, 0.01]), np.diag([1.0, 0.01]),
            error_budget=0.001,
        )
        self.assertEqual(result.selected_order, 1)
        self.assertLessEqual(result.theoretical_error_upper_bound, 0.001)

    def test_zero_budget_retains_effective_order(self) -> None:
        result = design_balanced_reduction(
            np.diag([0.8, 0.2]), np.diag([1.0, 0.1]), np.diag([1.0, 0.1]),
            error_budget=0.0,
        )
        self.assertEqual(result.selected_order, 2)
        self.assertAlmostEqual(result.theoretical_error_upper_bound, 0.0)

    def test_reduced_model_remains_stable(self) -> None:
        result = design_balanced_reduction(
            np.diag([0.9, 0.5, 0.1]), [[1.0], [0.2], [0.01]], [[1.0, 0.3, 0.01]],
            error_budget=0.1,
        )
        self.assertLess(result.reduced_spectral_radius, 1.0)

    def test_unstable_system_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            design_balanced_reduction([[1.01]], [[1.0]], [[1.0]], error_budget=0.1)


if __name__ == "__main__":
    unittest.main()
