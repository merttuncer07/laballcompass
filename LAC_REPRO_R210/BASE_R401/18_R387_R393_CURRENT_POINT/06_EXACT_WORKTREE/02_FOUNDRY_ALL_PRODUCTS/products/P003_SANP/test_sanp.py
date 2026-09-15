import unittest
import numpy as np

if __package__:
    from .sanp import construct_support_aware_neutral_portfolio, compare_with_raw_sample_on_fresh_returns
else:
    from sanp import construct_support_aware_neutral_portfolio, compare_with_raw_sample_on_fresh_returns


def sparse_covariance():
    covariance = np.eye(8) * 0.0004
    for i in range(0, 8, 2):
        covariance[i, i] = 0.0005 + 0.00005 * i
        covariance[i + 1, i + 1] = 0.0006 + 0.00004 * i
        covariance[i, i + 1] = covariance[i + 1, i] = 0.00020
    for i, j, value in [(0, 2, 0.00008), (2, 4, 0.00006), (4, 6, 0.00005)]:
        covariance[i, j] = covariance[j, i] = value
    return covariance


class SANPTests(unittest.TestCase):
    def _data(self):
        rng = np.random.default_rng(20260825)
        covariance = sparse_covariance()
        data = rng.multivariate_normal(np.zeros(8), covariance, size=535)
        return covariance, data[:35], data[35:185], data[185:]

    def _kwargs(self):
        return dict(
            factor_loadings=np.array([[-1.0, -0.7, -0.4, -0.1, 0.1, 0.4, 0.7, 1.0]]),
            target_factor_exposure=np.array([0.0]), lower_bounds=0.0, upper_bounds=0.35,
            risk_aversion=4.0,
        )

    def test_sacps_covariance_is_consumed_and_constraints_hold(self):
        covariance, train, validation, _ = self._data()
        result = construct_support_aware_neutral_portfolio(
            train, np.abs(covariance) > 0, np.zeros(8), covariance_validation_returns=validation, **self._kwargs()
        )
        self.assertEqual(result.status, "SUPPORT_AWARE_COVARIANCE_CONSUMED_BY_NEUTRAL_PORTFOLIO")
        self.assertEqual(result.covariance_model.unsupported_max_absolute_covariance, 0.0)
        self.assertLess(result.portfolio.maximum_constraint_residual, 1e-8)
        self.assertLess(abs(result.portfolio.factor_exposure[0]), 1e-8)
        self.assertAlmostEqual(result.portfolio.weights.sum(), 1.0, places=8)

    def test_composition_adds_factor_neutrality_missing_from_sacps_native_decision(self):
        covariance, train, validation, _ = self._data()
        factors = self._kwargs()["factor_loadings"]
        result = construct_support_aware_neutral_portfolio(
            train, np.abs(covariance) > 0, np.zeros(8), covariance_validation_returns=validation, **self._kwargs()
        )
        sacps_weights = np.asarray(result.covariance_model.minimum_variance_weights)
        self.assertGreater(abs(float((factors @ sacps_weights)[0])), 1e-3)
        self.assertLess(abs(result.portfolio.factor_exposure[0]), 1e-8)

    def test_fresh_risk_can_improve_over_raw_covariance_enpc(self):
        covariance, train, validation, fresh = self._data()
        result = construct_support_aware_neutral_portfolio(
            train, np.abs(covariance) > 0, np.zeros(8), covariance_validation_returns=validation, **self._kwargs()
        )
        comparison = compare_with_raw_sample_on_fresh_returns(
            result, train, np.zeros(8), fresh, **self._kwargs()
        )
        self.assertLess(comparison.support_aware_variance, comparison.raw_sample_variance)
        self.assertLess(comparison.variance_change_fraction_vs_raw, -0.05)

    def test_no_validation_segment_still_produces_feasible_portfolio(self):
        covariance, train, _, _ = self._data()
        result = construct_support_aware_neutral_portfolio(
            train, np.abs(covariance) > 0, np.zeros(8), **self._kwargs()
        )
        self.assertEqual(result.covariance_validation_cases, 0)
        self.assertLess(result.portfolio.maximum_constraint_residual, 1e-8)

    def test_dimension_mismatch_is_rejected(self):
        covariance, train, validation, _ = self._data()
        with self.assertRaises(ValueError):
            construct_support_aware_neutral_portfolio(
                train, np.abs(covariance) > 0, np.zeros(7), covariance_validation_returns=validation, **self._kwargs()
            )

    def test_invalid_support_is_not_silently_repaired(self):
        _, train, _, _ = self._data()
        mask = np.eye(8, dtype=bool); mask[0, 1] = True
        with self.assertRaises(ValueError):
            construct_support_aware_neutral_portfolio(train, mask, np.zeros(8), **self._kwargs())


if __name__ == "__main__":
    unittest.main()
