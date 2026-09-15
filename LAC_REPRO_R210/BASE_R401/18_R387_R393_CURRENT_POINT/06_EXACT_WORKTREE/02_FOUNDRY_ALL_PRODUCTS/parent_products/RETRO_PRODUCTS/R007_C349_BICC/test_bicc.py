import unittest

import numpy as np

from bicc import audit_concentration


class BICCTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(7)
        self.base = rng.uniform(0.0, 1.0, size=(4_000, 4))
        self.replacement = rng.uniform(0.0, 1.0, size=(4_000, 4))

    def test_linear_bounds_produce_conditional_certificate(self) -> None:
        weights = np.array([0.1, 0.2, 0.3, 0.4])
        result = audit_concentration(
            lambda row: float(weights @ row),
            self.base,
            self.replacement,
            global_coordinate_bounds=weights,
        )
        self.assertEqual(result.certificate_status, "ASSUMPTION_CONDITIONAL_CERTIFICATE")
        self.assertAlmostEqual(result.supplied_bound_square_sum, 0.3)
        self.assertTrue(all(not item.observed_bound_violation for item in result.influences))

    def test_bad_bound_is_falsified(self) -> None:
        result = audit_concentration(
            lambda row: float(row[0]),
            self.base,
            self.replacement,
            global_coordinate_bounds=[0.05, 0.0, 0.0, 0.0],
        )
        self.assertEqual(result.certificate_status, "OBSERVED_BOUND_VIOLATION")
        self.assertTrue(result.influences[0].observed_bound_violation)

    def test_no_global_bounds_stays_empirical(self) -> None:
        result = audit_concentration(lambda row: float(np.mean(row)), self.base, self.replacement)
        self.assertEqual(result.certificate_status, "EMPIRICAL_INFLUENCE_ONLY")
        self.assertIsNone(result.mcdiarmid_two_sided_radius)
        self.assertIsNone(result.mcdiarmid_two_sided_tail_bound(0.2))

    def test_distributed_influence_has_more_effective_coordinates(self) -> None:
        even = audit_concentration(
            lambda row: float(np.mean(row)), self.base, self.replacement,
            global_coordinate_bounds=[0.25] * 4,
        )
        concentrated = audit_concentration(
            lambda row: float(0.85 * row[0] + 0.05 * np.sum(row[1:])), self.base, self.replacement,
            global_coordinate_bounds=[0.85, 0.05, 0.05, 0.05],
        )
        self.assertGreater(even.effective_coordinates, concentrated.effective_coordinates)
        self.assertLess(even.mcdiarmid_two_sided_radius, concentrated.mcdiarmid_two_sided_radius)



class CertificateRepairTests(unittest.TestCase):
    def test_observed_violation_removes_radius_and_tail_guarantees(self):
        r=audit_concentration(lambda x:float(x[0]),[[0.],[0.]],[[1.],[1.]],global_coordinate_bounds=[.1])
        self.assertEqual(r.certificate_status,'OBSERVED_BOUND_VIOLATION')
        self.assertIsNone(r.mcdiarmid_two_sided_radius)
        self.assertIsNone(r.mcdiarmid_two_sided_tail_bound(1.))

    def test_single_deterministic_probe_has_sensitivity_but_no_probability_certificate(self):
        r=audit_concentration(lambda x:float(x[0]+x[1]),[[1.,1.]],[[0.,0.]],
            global_coordinate_bounds=[1.,1.],sampling_model='scenario_pairs')
        self.assertEqual([i.rms_replacement_effect for i in r.influences],[1.,1.])
        self.assertEqual(r.certificate_status,'EMPIRICAL_SCENARIO_INFLUENCE')
        self.assertIsNone(r.efron_stein_variance_upper_proxy)
        self.assertIsNone(r.mcdiarmid_two_sided_radius)
        self.assertIsNone(r.mcdiarmid_two_sided_tail_bound(1.))

    def test_invalid_tolerance_cannot_hide_observed_violation(self):
        for tolerance in (float('nan'),float('inf'),-1.):
            with self.assertRaises(ValueError):
                audit_concentration(lambda x:float(x[0]),[[0.],[0.]],[[1.],[1.]],
                    global_coordinate_bounds=[.1],violation_tolerance=tolerance)

if __name__ == "__main__":
    unittest.main()
