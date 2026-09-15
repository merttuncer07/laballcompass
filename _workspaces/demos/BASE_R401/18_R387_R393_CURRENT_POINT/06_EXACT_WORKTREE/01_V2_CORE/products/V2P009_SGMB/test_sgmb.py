import unittest
from sgmb import _multifidelity_allocation, support_gated_multifidelity_monitoring


def kwargs(month):
    return dict(
        cohort_size=10000,
        base_rates=[0.03] * 24,
        propensity_multipliers=[0.2, 1.0, 5.0],
        initial_class_weights=[0.3, 0.4, 0.3],
        month=month,
        total_budget=200.0,
        fine_cost=5.0,
        cheap_cost=1.0,
        pilot_correlation=0.95,
        min_fine=10,
        fragile_ess_fraction=0.8,
    )


class SGMBTests(unittest.TestCase):
    def test_early_supported_month_allows_multifidelity(self):
        r = support_gated_multifidelity_monitoring(**kwargs(1))
        self.assertEqual(r.support_status, "SUPPORT_USABLE")
        self.assertTrue(r.support_gate_open)
        self.assertEqual(r.mode, "multifidelity")
        self.assertGreater(r.n_cheap, 0)

    def test_late_fragile_month_forces_fine_only(self):
        r = support_gated_multifidelity_monitoring(**kwargs(24))
        self.assertEqual(r.support_status, "SUPPORT_FRAGILE")
        self.assertFalse(r.support_gate_open)
        self.assertEqual(r.mode, "fine_only")
        self.assertEqual(r.n_cheap, 0)

    def test_fragile_gate_overrides_high_correlation(self):
        k = kwargs(24); k["pilot_correlation"] = 0.999
        r = support_gated_multifidelity_monitoring(**k)
        self.assertEqual(r.n_cheap, 0)

    def test_supported_branch_matches_k048_count_allocator(self):
        k = kwargs(1)
        p = _multifidelity_allocation(k["total_budget"], k["fine_cost"], k["cheap_cost"], k["pilot_correlation"], k["min_fine"])
        r = support_gated_multifidelity_monitoring(**k)
        self.assertEqual((r.n_fine, r.n_cheap), (p["n_fine"], p["n_cheap"]))
        self.assertAlmostEqual(r.variance_proxy, p["variance_proxy"])

    def test_low_correlation_routes_fine_only_even_with_support(self):
        k = kwargs(1); k["pilot_correlation"] = 0.05
        r = support_gated_multifidelity_monitoring(**k)
        self.assertEqual(r.mode, "fine_only")
        self.assertEqual(r.n_cheap, 0)

    def test_budget_respected_supported(self):
        r = support_gated_multifidelity_monitoring(**kwargs(1))
        self.assertLessEqual(r.spent_budget, 200.0)

    def test_budget_respected_fragile(self):
        r = support_gated_multifidelity_monitoring(**kwargs(24))
        self.assertLessEqual(r.spent_budget, 200.0)

    def test_support_degrades_across_declared_burnout_shell(self):
        early = support_gated_multifidelity_monitoring(**kwargs(1))
        late = support_gated_multifidelity_monitoring(**kwargs(24))
        self.assertGreater(early.effective_sample_fraction, late.effective_sample_fraction)

    def test_budget_too_small_returns_unfunded(self):
        k = kwargs(1); k["total_budget"] = 2.0
        r = support_gated_multifidelity_monitoring(**k)
        self.assertEqual(r.mode, "unfunded")
        self.assertEqual((r.n_fine, r.n_cheap), (0, 0))

    def test_negative_month_rejected(self):
        k = kwargs(1); k["month"] = -1
        with self.assertRaises(ValueError): support_gated_multifidelity_monitoring(**k)

    def test_mechanism_removing_comparator_would_use_unsupported_cheap_channel(self):
        k = kwargs(24)
        blind = _multifidelity_allocation(k["total_budget"], k["fine_cost"], k["cheap_cost"], k["pilot_correlation"], k["min_fine"])
        guarded = support_gated_multifidelity_monitoring(**k)
        self.assertGreater(blind["n_cheap"], 0)
        self.assertEqual(guarded.n_cheap, 0)

    def test_threshold_change_moves_same_month_across_gate(self):
        strict = kwargs(12); strict["fragile_ess_fraction"] = 0.8
        loose = kwargs(12); loose["fragile_ess_fraction"] = 0.7
        a = support_gated_multifidelity_monitoring(**strict)
        b = support_gated_multifidelity_monitoring(**loose)
        self.assertEqual(a.support_status, "SUPPORT_FRAGILE")
        self.assertEqual(b.support_status, "SUPPORT_USABLE")


if __name__ == '__main__': unittest.main()
