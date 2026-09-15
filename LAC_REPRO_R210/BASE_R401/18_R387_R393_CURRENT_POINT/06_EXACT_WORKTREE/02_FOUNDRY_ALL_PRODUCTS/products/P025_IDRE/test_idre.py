import unittest
if __package__:
    from .idre import identification_driven_envelope
else:
    from idre import identification_driven_envelope


class IDRETests(unittest.TestCase):
    def test_uncertainty_can_revoke_certificate(self):
        r = identification_driven_envelope(-0.2, 0.03, horizon=8, disturbance_bound=0.22, decision_gap=1.0)
        self.assertTrue(r.nominal_certified)
        self.assertFalse(r.conservative_certified)
        self.assertIn("REVOKES", r.status)

    def test_stable_system_survives(self):
        r = identification_driven_envelope(-0.8, 0.01, horizon=8, disturbance_bound=0.18, decision_gap=1.0)
        self.assertTrue(r.conservative_certified)

    def test_zero_rate_limit(self):
        r = identification_driven_envelope(0, 0, horizon=2, disturbance_bound=.2, decision_gap=1)
        self.assertAlmostEqual(r.nominal_flip_index, .4)

    def test_invalid_gap_rejected(self):
        with self.assertRaises(ValueError):
            identification_driven_envelope(-.2, .1, horizon=1, disturbance_bound=1, decision_gap=0)


if __name__ == "__main__": unittest.main()
