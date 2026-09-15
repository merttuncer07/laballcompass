import unittest

from demo_failure_architecture import build_designer


class MFPATests(unittest.TestCase):
    def test_late_route_needs_activation_bridge(self):
        designer = build_designer()
        result = designer.evaluate({"phase_transformation": 1.0})
        self.assertEqual(result.activated_routes["nominal"], ())
        self.assertAlmostEqual(result.worst_case_energy, 1.0)

    def test_optimizer_respects_equal_mass_budget(self):
        result = build_designer().optimize(1.0, 0.05)
        self.assertAlmostEqual(sum(result.allocation.values()), 1.0)

    def test_composed_architecture_beats_single_route_worst_case(self):
        designer = build_designer()
        composed = designer.optimize(1.0, 0.05)
        single = designer.best_single_route(1.0)
        self.assertGreater(composed.worst_case_energy, single.worst_case_energy)
        self.assertGreater(sum(mass > 0 for mass in composed.allocation.values()), 1)


if __name__ == "__main__":
    unittest.main()

