import unittest
import numpy as np

from idasro import identification_admissible_shift_robust_decision


class IDASROTests(unittest.TestCase):
    def base(self, **kw):
        args=dict(
            persistence=-0.2,persistence_se=0.03,horizon=8,disturbance_bound=0.22,decision_gap=1.0,
            mean_vector_at_estimate=[0.12,0.50],mean_sensitivity_to_persistence=[3.0,0.0],
            z_score=1.96,sensitivity_shell_certified=True,sensitivity_provenance="DECLARED_SYNTHETIC_AFFINE_MAP_V1",
        )
        args.update(kw)
        return identification_admissible_shift_robust_decision(**args)

    # Four P025 invariant-preservation cases.
    def test_p025_uncertainty_can_revoke_certificate(self):
        r=self.base()
        self.assertTrue(r.identification_envelope.nominal_certified)
        self.assertFalse(r.identification_envelope.conservative_certified)
        self.assertIn("REVOKES",r.identification_envelope.status)

    def test_p025_stable_system_survives(self):
        r=self.base(persistence=-0.8,persistence_se=0.01,disturbance_bound=0.18)
        self.assertTrue(r.identification_envelope.conservative_certified)

    def test_p025_zero_rate_limit_preserved(self):
        r=self.base(persistence=0.0,persistence_se=0.0,horizon=2,disturbance_bound=0.2,mean_sensitivity_to_persistence=[0.0,0.0])
        self.assertAlmostEqual(r.identification_envelope.nominal_flip_index,0.4)

    def test_p025_invalid_gap_rejected(self):
        with self.assertRaises(ValueError): self.base(decision_gap=0.0)

    # Eight bridge / K068 boundary cases.
    def test_exact_radius_mapping_from_scalar_identification_interval(self):
        r=self.base()
        self.assertAlmostEqual(r.decision.persistence_radius,1.96*0.03)
        self.assertAlmostEqual(r.decision.mean_space_radius,1.96*0.03*3.0)
        np.testing.assert_allclose(r.decision.normalized_shift_direction,[1.0,0.0],atol=1e-12)

    def test_directional_robust_solution_soft_thresholds_parallel_component(self):
        r=self.base()
        # radius 0.1764 exceeds the 0.12 parallel nominal coefficient.
        np.testing.assert_allclose(r.decision.robust_decision,[0.0,0.5],atol=1e-10)
        self.assertGreater(r.decision.worst_case_objective_gain,0.0)

    def test_orthogonal_component_is_unchanged(self):
        r=self.base(mean_vector_at_estimate=[0.4,0.3],mean_sensitivity_to_persistence=[1.0,1.0])
        v=np.asarray(r.decision.normalized_shift_direction)
        nominal=np.asarray(r.decision.nominal_decision); robust=np.asarray(r.decision.robust_decision)
        nominal_perp=nominal-v*(v@nominal); robust_perp=robust-v*(v@robust)
        np.testing.assert_allclose(nominal_perp,robust_perp,atol=1e-10)

    def test_missing_sensitivity_certificate_fails_closed(self):
        r=self.base(sensitivity_shell_certified=False,sensitivity_provenance=None)
        self.assertIsNone(r.decision.robust_decision)
        self.assertEqual(r.status,"IDENTIFICATION_ENVELOPE_ONLY_BRIDGE_REFUSED")

    def test_certified_shell_requires_provenance(self):
        with self.assertRaises(ValueError): self.base(sensitivity_provenance="")

    def test_zero_sensitivity_exactly_reuses_nominal_action(self):
        r=self.base(mean_sensitivity_to_persistence=[0.0,0.0])
        np.testing.assert_allclose(r.decision.robust_decision,r.decision.nominal_decision,atol=0)
        self.assertEqual(r.decision.mean_space_radius,0.0)
        self.assertEqual(r.decision.worst_case_objective_gain,0.0)

    def test_larger_identification_se_never_increases_parallel_exposure(self):
        small=self.base(persistence_se=0.005,mean_vector_at_estimate=[0.5,0.2],mean_sensitivity_to_persistence=[1.0,0.0])
        large=self.base(persistence_se=0.08,mean_vector_at_estimate=[0.5,0.2],mean_sensitivity_to_persistence=[1.0,0.0])
        self.assertLessEqual(abs(large.decision.robust_decision[0]),abs(small.decision.robust_decision[0])+1e-12)

    def test_invalid_vector_or_z_contract_is_rejected(self):
        with self.assertRaises(ValueError): self.base(mean_sensitivity_to_persistence=[1.0])
        with self.assertRaises(ValueError): self.base(z_score=-1.0)


if __name__ == '__main__': unittest.main()
