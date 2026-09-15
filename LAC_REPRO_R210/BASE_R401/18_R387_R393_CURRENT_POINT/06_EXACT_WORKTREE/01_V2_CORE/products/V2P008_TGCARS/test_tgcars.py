import math
import unittest

from tgcars import (
    FeatureSpec,
    ResolutionOption,
    allocate_certificate_aware_resolution,
    audit_guarantee_transport,
    transport_gated_certificate_aware_resolution,
)


def shell():
    features = [
        FeatureSpec("critical", 1.0, 0.08, 1.0),
        FeatureSpec("secondary", 0.6, 0.08, 1.0),
        FeatureSpec("nuisance", 0.95, 0.19, 20.0),
    ]
    options = [
        ResolutionOption("coarse", 1.0, 1.0, 0.0),
        ResolutionOption("fine", 3.0, 0.1, 0.0),
    ]
    source = [-1.0, -0.5, 0.0, 0.5, 1.0] * 4
    return features, options, source


class TGCARSTests(unittest.TestCase):
    def test_stable_transport_preserves_exact_p135_allocation(self):
        f, o, source = shell()
        blind = allocate_certificate_aware_resolution(f, protected_margin=0.19, options=o, budget=5.0)
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=source,
            max_transport_score=0.2,
        )
        self.assertTrue(got.transport_audit.accepted)
        self.assertEqual(got.allocation, blind.allocation)
        self.assertEqual(got.consequence_weights, blind.consequence_weights)
        self.assertFalse(got.fallback_used)

    def test_mean_shift_disables_certificate_zeroing(self):
        f, o, source = shell()
        target = [x + 2.0 for x in source]
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=target,
            max_transport_score=0.5,
        )
        self.assertFalse(got.transport_audit.accepted)
        self.assertFalse(got.certificate_zeroing_enabled)
        self.assertGreater(got.consequence_weights["nuisance"], 0.0)

    def test_scale_shift_disables_certificate_zeroing(self):
        f, o, source = shell()
        target = [3.0 * x for x in source]
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=target,
            max_transport_score=0.5,
        )
        self.assertFalse(got.transport_audit.accepted)
        self.assertGreater(got.transport_audit.log_scale_shift, 1.0)

    def test_driver_dependence_can_break_transport_even_without_marginal_shift(self):
        f, o, source = shell()
        target = list(source)
        driver = list(target)
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=target,
            target_driver=driver, max_transport_score=0.5,
        )
        self.assertFalse(got.transport_audit.accepted)
        self.assertGreater(got.transport_audit.target_residual_driver_correlation, 0.99)

    def test_insufficient_support_fails_closed(self):
        f, o, _ = shell()
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=[-1, 0, 1], target_residuals=[-1, 0, 1],
            max_transport_score=1.0, min_samples=8,
        )
        self.assertEqual(got.transport_audit.reason, "INSUFFICIENT_RESIDUAL_SUPPORT")
        self.assertTrue(got.fallback_used)

    def test_degenerate_source_scale_fails_closed(self):
        f, o, _ = shell()
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=[1.0] * 10, target_residuals=[1.0] * 10,
            max_transport_score=1.0,
        )
        self.assertEqual(got.transport_audit.reason, "SOURCE_RESIDUAL_SCALE_UNIDENTIFIED")
        self.assertTrue(got.fallback_used)

    def test_target_driver_shape_mismatch_fails_closed(self):
        f, o, source = shell()
        a = audit_guarantee_transport(source, source, target_driver=[1, 2], max_transport_score=1.0)
        self.assertFalse(a.accepted)
        self.assertEqual(a.reason, "TARGET_DRIVER_SHAPE_MISMATCH")

    def test_fallback_changes_resolution_when_deleted_feature_would_dominate_if_nonzero(self):
        f, o, source = shell()
        blind = allocate_certificate_aware_resolution(f, protected_margin=0.19, options=o, budget=5.0)
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=[x + 2 for x in source],
            max_transport_score=0.5,
        )
        blind_map = {x["region"]: x["option"] for x in blind.allocation["allocations"]}
        got_map = {x["region"]: x["option"] for x in got.allocation["allocations"]}
        self.assertEqual(blind_map["nuisance"], "coarse")
        self.assertEqual(got_map["nuisance"], "fine")

    def test_budget_is_respected_in_both_branches(self):
        f, o, source = shell()
        stable = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=source,
            max_transport_score=0.2,
        )
        shifted = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=[x + 2 for x in source],
            max_transport_score=0.5,
        )
        self.assertLessEqual(stable.allocation["total_cost"], 5.0)
        self.assertLessEqual(shifted.allocation["total_cost"], 5.0)

    def test_boundary_is_inclusive(self):
        _, _, source = shell()
        a = audit_guarantee_transport(source, source, max_transport_score=0.0)
        self.assertTrue(a.accepted)
        self.assertEqual(a.residual_shift_score, 0.0)

    def test_nonfinite_residuals_fail_closed(self):
        f, o, source = shell()
        target = list(source); target[0] = math.nan
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=target,
            max_transport_score=1.0,
        )
        self.assertFalse(got.transport_audit.accepted)
        self.assertEqual(got.transport_audit.reason, "NONFINITE_RESIDUALS")

    def test_certificate_identity_is_preserved_for_audit(self):
        f, o, source = shell()
        got = transport_gated_certificate_aware_resolution(
            f, protected_margin=0.19, options=o, budget=5.0,
            source_residuals=source, target_residuals=[x + 2 for x in source],
            max_transport_score=0.5,
        )
        self.assertIn("nuisance", got.certificate["deleted_features"])
        self.assertIn("revalidation", got.status.lower())


if __name__ == "__main__":
    unittest.main()
