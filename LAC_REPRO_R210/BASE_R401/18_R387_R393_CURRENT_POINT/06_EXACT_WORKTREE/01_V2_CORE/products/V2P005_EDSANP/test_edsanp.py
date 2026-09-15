import unittest
import numpy as np

from edsanp import SupportEvidence, construct_effective_diversity_gated_portfolio, compare_gated_with_raw_on_fresh_returns


def sparse_covariance():
    covariance = np.eye(8) * 0.0004
    for i in range(0, 8, 2):
        covariance[i, i] = 0.0005 + 0.00005 * i
        covariance[i + 1, i + 1] = 0.0006 + 0.00004 * i
        covariance[i, i + 1] = covariance[i + 1, i] = 0.00020
    for i, j, value in [(0, 2, 0.00008), (2, 4, 0.00006), (4, 6, 0.00005)]:
        covariance[i, j] = covariance[j, i] = value
    return covariance


def mask_evidence(mask, *, n=80, rho=0.001):
    p = len(mask)
    return {(i, j): SupportEvidence(n, rho) for i in range(p) for j in range(i + 1, p)}


class EDSANPTests(unittest.TestCase):
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

    def _strong(self, covariance, train, validation=None):
        mask = np.abs(covariance) > 0
        return construct_effective_diversity_gated_portfolio(
            train, mask, mask_evidence(mask), np.zeros(8),
            covariance_validation_returns=validation, **self._kwargs()
        )

    # Six P003 invariant-preservation cases.
    def test_p003_covariance_is_consumed_and_constraints_hold_when_gate_passes(self):
        covariance, train, validation, _ = self._data(); r = self._strong(covariance, train, validation)
        self.assertEqual(r.route, "SUPPORT_AWARE_SANP")
        self.assertEqual(r.structured_result.covariance_model.unsupported_max_absolute_covariance, 0.0)
        self.assertLess(r.portfolio.maximum_constraint_residual, 1e-8)
        self.assertAlmostEqual(r.portfolio.weights.sum(), 1.0, places=8)

    def test_p003_factor_neutrality_is_preserved(self):
        covariance, train, validation, _ = self._data(); r = self._strong(covariance, train, validation)
        self.assertLess(abs(r.portfolio.factor_exposure[0]), 1e-8)
        sacps_weights = np.asarray(r.structured_result.covariance_model.minimum_variance_weights)
        self.assertGreater(abs(float((self._kwargs()["factor_loadings"] @ sacps_weights)[0])), 1e-3)

    def test_p003_fresh_risk_improvement_remains_possible(self):
        covariance, train, validation, fresh = self._data(); r = self._strong(covariance, train, validation)
        c = compare_gated_with_raw_on_fresh_returns(r, train, np.zeros(8), fresh, **self._kwargs())
        self.assertLess(c["gated_variance"], c["raw_variance"])
        self.assertLess(c["variance_change_fraction_vs_raw"], -0.05)

    def test_p003_no_validation_segment_still_feasible(self):
        covariance, train, _, _ = self._data(); r = self._strong(covariance, train)
        self.assertEqual(r.structured_result.covariance_validation_cases, 0)
        self.assertLess(r.portfolio.maximum_constraint_residual, 1e-8)

    def test_p003_dimension_mismatch_is_rejected(self):
        covariance, train, validation, _ = self._data(); mask = np.abs(covariance) > 0
        with self.assertRaises(ValueError):
            construct_effective_diversity_gated_portfolio(train, mask, mask_evidence(mask), np.zeros(7), covariance_validation_returns=validation, **self._kwargs())

    def test_p003_invalid_support_is_not_silently_repaired(self):
        _, train, _, _ = self._data(); mask = np.eye(8, dtype=bool); mask[0, 1] = True
        with self.assertRaises(ValueError):
            construct_effective_diversity_gated_portfolio(train, mask, {}, np.zeros(8), **self._kwargs())

    # Six K019-specific boundary cases.
    def test_nominally_many_but_correlated_evidence_routes_to_raw_fallback(self):
        covariance, train, validation, _ = self._data(); mask = np.abs(covariance) > 0
        ev = mask_evidence(mask, n=100, rho=0.05)
        r = construct_effective_diversity_gated_portfolio(train, mask, ev, np.zeros(8), covariance_validation_returns=validation, min_effective_count=20, max_variance_inflation=10, **self._kwargs())
        self.assertEqual(r.route, "RAW_COVARIANCE_ENPC_FALLBACK")
        self.assertTrue(r.failed_pairs)
        self.assertLess(r.support_checks[0].effective_independent_count, 20)

    def test_same_nominal_count_with_low_dependence_allows_structured_path(self):
        covariance, train, validation, _ = self._data(); mask = np.abs(covariance) > 0
        ev = mask_evidence(mask, n=100, rho=0.001)
        r = construct_effective_diversity_gated_portfolio(train, mask, ev, np.zeros(8), covariance_validation_returns=validation, min_effective_count=20, max_variance_inflation=2, **self._kwargs())
        self.assertEqual(r.route, "SUPPORT_AWARE_SANP")
        self.assertTrue(all(x.passes_gate for x in r.support_checks))

    def test_pairwise_small_can_still_fail_collective_variance_gate(self):
        covariance, train, _, _ = self._data(); mask = np.abs(covariance) > 0
        ev = mask_evidence(mask, n=200, rho=0.009)
        r = construct_effective_diversity_gated_portfolio(train, mask, ev, np.zeros(8), pairwise_threshold=.01, max_variance_inflation=2.0, min_effective_count=10, **self._kwargs())
        self.assertEqual(r.route, "RAW_COVARIANCE_ENPC_FALLBACK")
        self.assertTrue(r.support_checks[0].pairwise_threshold_says_small)
        self.assertTrue(r.support_checks[0].collective_risk_flag)

    def test_missing_support_evidence_fails_closed_without_editing_mask(self):
        covariance, train, _, _ = self._data(); mask = np.abs(covariance) > 0
        ev = mask_evidence(mask); ev.pop(next(iter(ev)))
        r = construct_effective_diversity_gated_portfolio(train, mask, ev, np.zeros(8), **self._kwargs())
        self.assertEqual(r.route, "RAW_COVARIANCE_ENPC_FALLBACK")
        self.assertEqual(len(r.missing_pairs), 1)
        self.assertIsNone(r.structured_result)

    def test_diagonal_evidence_key_is_rejected(self):
        _, train, _, _ = self._data(); mask = np.eye(8, dtype=bool)
        ev = mask_evidence(mask); ev[(0, 0)] = SupportEvidence(100, 0.0)
        with self.assertRaises(ValueError):
            construct_effective_diversity_gated_portfolio(train, mask, ev, np.zeros(8), **self._kwargs())

    def test_diagonal_only_mask_still_requires_evidence_for_absence_decisions(self):
        _, train, validation, _ = self._data(); mask = np.eye(8, dtype=bool)
        missing = construct_effective_diversity_gated_portfolio(train, mask, {}, np.zeros(8), covariance_validation_returns=validation, **self._kwargs())
        self.assertEqual(missing.route, "RAW_COVARIANCE_ENPC_FALLBACK")
        r = construct_effective_diversity_gated_portfolio(train, mask, mask_evidence(mask), np.zeros(8), covariance_validation_returns=validation, **self._kwargs())
        self.assertEqual(r.route, "SUPPORT_AWARE_SANP")
        self.assertEqual(len(r.support_checks), 28)
        self.assertTrue(all(not x.mask_supports_relation for x in r.support_checks))


if __name__ == "__main__":
    unittest.main()
