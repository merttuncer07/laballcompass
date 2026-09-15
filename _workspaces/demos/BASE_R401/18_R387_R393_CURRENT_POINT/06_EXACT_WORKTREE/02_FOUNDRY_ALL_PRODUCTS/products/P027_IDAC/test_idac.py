import unittest
if __package__:
    from .idac import audit_series_deployment
else:
    from idac import audit_series_deployment


class IDACTests(unittest.TestCase):
    def test_unit_yield_integer_rhs_certified(self): self.assertTrue(audit_series_deployment(30,[50,30],[1,1]).theorem_certificate)
    def test_fractional_yield_drops_theorem(self): self.assertFalse(audit_series_deployment(30,[50,30],[.5,1]).theorem_certificate)
    def test_integral_observation_not_theorem(self):
        r=audit_series_deployment(30,[50,30],[.5,1]); self.assertTrue(r.observed_lp_integral); self.assertFalse(r.theorem_certificate)
    def test_fractional_optimum_gap(self): self.assertAlmostEqual(audit_series_deployment(31,[50,30],[.75,1]).integrality_gap,.25)


if __name__ == '__main__': unittest.main()
