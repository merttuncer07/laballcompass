import unittest

import numpy as np

from sacps import estimate_support_aware_covariance


class Tests(unittest.TestCase):
    def test_support_is_exact_and_covariance_is_positive_definite(self):
        rng = np.random.default_rng(2)
        data = rng.normal(size=(30, 5))
        mask = np.eye(5, dtype=bool); mask[0:2, 0:2] = True
        result = estimate_support_aware_covariance(data, mask)
        self.assertEqual(result.unsupported_max_absolute_covariance, 0.0)
        self.assertGreater(result.minimum_eigenvalue, 0)
        self.assertAlmostEqual(sum(result.minimum_variance_weights), 1.0)

    def test_high_dimensional_singular_sample_can_be_regularized(self):
        rng = np.random.default_rng(5)
        data = rng.normal(size=(8, 12))
        result = estimate_support_aware_covariance(data, np.eye(12, dtype=bool))
        self.assertTrue(np.isfinite(result.condition_number))
        self.assertEqual(result.status, "SUPPORTED_COVARIANCE_AND_DECISION_READY")

    def test_holdout_produces_realized_decision_diagnostic(self):
        rng = np.random.default_rng(4)
        train = rng.normal(size=(40, 4)); holdout = rng.normal(size=(100, 4))
        result = estimate_support_aware_covariance(train, np.ones((4, 4), bool), holdout_returns=holdout)
        self.assertIsNotNone(result.realized_holdout_variance)
        self.assertGreaterEqual(result.realized_holdout_variance, 0)
        self.assertGreater(len(result.gaussian_validation_scores), 0)

    def test_asymmetric_support_is_rejected(self):
        mask = np.eye(3, dtype=bool); mask[0, 1] = True
        with self.assertRaises(ValueError):
            estimate_support_aware_covariance(np.ones((5, 3)), mask)


if __name__ == "__main__":
    unittest.main()
