import unittest

import numpy as np

from enpc import construct_portfolio


class ENPCTests(unittest.TestCase):
    def test_factor_exposure_is_neutralized(self):
        mu = np.array([0.1, 0.08, 0.02])
        covariance = np.eye(3) * 0.1
        factors = np.array([[1.0, 0.0, -1.0]])
        result = construct_portfolio(mu, covariance, factors, np.array([0.0]))
        self.assertLess(abs(result.factor_exposure[0]), 1e-9)
        self.assertLess(result.budget_residual, 1e-9)

    def test_infeasible_exposure_is_reported(self):
        with self.assertRaises(ValueError):
            construct_portfolio(
                np.array([0.1, 0.2]),
                np.eye(2),
                np.ones((1, 2)),
                np.array([0.0]),
                budget=1.0,
                lower_bounds=0.0,
                upper_bounds=1.0,
            )

    def test_non_psd_covariance_is_rejected(self):
        with self.assertRaises(ValueError):
            construct_portfolio(np.zeros(2), np.array([[1.0, 2.0], [2.0, 1.0]]))

    def test_unconstrained_mode_retains_budget(self):
        result = construct_portfolio(np.array([0.1, 0.05]), np.eye(2) * 0.2)
        self.assertAlmostEqual(result.weights.sum(), 1.0)


if __name__ == "__main__":
    unittest.main()

