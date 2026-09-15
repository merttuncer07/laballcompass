import unittest

import numpy as np

from cbac import design_balanced_assignment


class CBACTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(50)
        self.x = rng.normal(size=(40, 4))

    def test_arm_sizes_are_exact(self) -> None:
        result = design_balanced_assignment(self.x, treated_count=17, randomization_draws=500, seed=1)
        self.assertEqual(sum(result.assignment), 17)
        self.assertEqual(result.control_count, 23)

    def test_selected_assignment_lies_inside_acceptance_region(self) -> None:
        result = design_balanced_assignment(
            self.x, treated_count=20, randomization_draws=1000, acceptance_fraction=0.05, seed=2
        )
        self.assertLessEqual(result.mahalanobis_distance, result.acceptance_cutoff + 1e-12)
        self.assertLessEqual(result.distance_percentile, 0.051)

    def test_constant_covariate_is_reported_and_ignored(self) -> None:
        x = np.column_stack([self.x, np.ones(40)])
        result = design_balanced_assignment(x, treated_count=20, randomization_draws=300, seed=3)
        self.assertEqual(result.constant_covariate_indices, (4,))
        self.assertEqual(result.standardized_mean_differences[4], 0.0)

    def test_invalid_arm_size_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            design_balanced_assignment(self.x, treated_count=40)


if __name__ == "__main__":
    unittest.main()
