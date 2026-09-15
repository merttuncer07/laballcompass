from __future__ import annotations

import unittest

from tsrc import FeatureSpec, TargetSufficientReductionCertifier


class TargetSufficientReductionCertifierTests(unittest.TestCase):
    def test_deletes_low_impact_feature(self) -> None:
        certifier = TargetSufficientReductionCertifier(
            [FeatureSpec("core", 2.0, 1.0, 1.0), FeatureSpec("detail", 0.1, 1.0, 2.0)]
        )
        certificate = certifier.optimize(0.5)
        self.assertIn("detail", certificate.deleted_features)
        self.assertNotIn("core", certificate.deleted_features)
        self.assertTrue(certificate.action_invariant)

    def test_optimizer_respects_error_budget(self) -> None:
        certifier = TargetSufficientReductionCertifier(
            [
                FeatureSpec("a", 0.2, 1.0, 5.0),
                FeatureSpec("b", 0.3, 1.0, 6.0),
                FeatureSpec("c", 1.0, 1.0, 20.0),
            ]
        )
        certificate = certifier.optimize(0.6, reserve=0.1)
        self.assertLessEqual(certificate.score_error_bound, 0.5 + 1e-12)

    def test_evaluation_reports_no_action_change_when_certificate_holds(self) -> None:
        certifier = TargetSufficientReductionCertifier(
            [FeatureSpec("core", 1.0, 2.0), FeatureSpec("detail", 0.1, 0.5)]
        )
        certificate = certifier.optimize(0.8)
        evaluated = certifier.evaluate(certificate, [[-2, 0.2], [2, -0.2]])
        self.assertEqual(evaluated.observed_action_changes, 0)

    def test_evaluation_rejects_values_outside_declared_deletion_shell(self) -> None:
        certifier = TargetSufficientReductionCertifier(
            [FeatureSpec("detail", 0.1, 0.5, 1.0)]
        )
        certificate = certifier.optimize(1.0)
        with self.assertRaises(ValueError):
            certifier.evaluate(certificate, [[2.0]])


if __name__ == "__main__":
    unittest.main()
