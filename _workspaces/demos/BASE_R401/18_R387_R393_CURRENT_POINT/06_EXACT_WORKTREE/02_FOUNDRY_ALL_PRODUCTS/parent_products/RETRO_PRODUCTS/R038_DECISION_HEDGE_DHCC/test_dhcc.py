import unittest

import numpy as np

from dhcc import calibrate_hedge_covariance


class Tests(unittest.TestCase):
    def test_selected_candidate_minimizes_declared_decision_loss(self):
        rng = np.random.default_rng(3)
        x1 = rng.normal(size=(40, 2)); y1 = x1 @ [1, -.5] + rng.normal(scale=.3, size=40)
        x2 = rng.normal(size=(100, 2)); y2 = x2 @ [1, -.5] + rng.normal(scale=.3, size=100)
        result = calibrate_hedge_covariance(y1, x1, y2, x2, ridge_grid=[0, .01, .1, 1])
        self.assertAlmostEqual(result.selected.validation_decision_loss, min(c.validation_decision_loss for c in result.candidates))
        self.assertAlmostEqual(len(result.selected.hedge_coefficients), 2)

    def test_collinear_hedges_are_stabilized(self):
        rng = np.random.default_rng(8)
        z = rng.normal(size=20); x1 = np.column_stack([z, z + rng.normal(scale=.001, size=20)])
        y1 = z + rng.normal(scale=.2, size=20)
        zv = rng.normal(size=300); x2 = np.column_stack([zv, zv + rng.normal(scale=.2, size=300)])
        y2 = zv + rng.normal(scale=.2, size=300)
        result = calibrate_hedge_covariance(y1, x1, y2, x2, ridge_grid=[0, .001, .01, .1, 1])
        self.assertLessEqual(result.selected.validation_residual_variance, result.unregularized_validation_variance + 1e-12)
        self.assertTrue(np.isfinite(result.selected.hedge_condition_number))

    def test_turnover_penalty_changes_declared_loss(self):
        rng = np.random.default_rng(5)
        x1 = rng.normal(size=(30, 2)); y1 = x1[:, 0] + rng.normal(scale=.2, size=30)
        x2 = rng.normal(size=(60, 2)); y2 = x2[:, 0] + rng.normal(scale=.2, size=60)
        result = calibrate_hedge_covariance(y1, x1, y2, x2, ridge_grid=[0, .1, 1, 10], turnover_penalty=1.0)
        self.assertAlmostEqual(result.selected.validation_decision_loss, result.selected.validation_residual_variance + result.selected.turnover)

    def test_mismatched_validation_columns_are_rejected(self):
        with self.assertRaises(ValueError):
            calibrate_hedge_covariance([1, 2, 3], [[1], [2], [3]], [1, 2], [[1, 2], [2, 3]], ridge_grid=[0])


if __name__ == "__main__":
    unittest.main()
