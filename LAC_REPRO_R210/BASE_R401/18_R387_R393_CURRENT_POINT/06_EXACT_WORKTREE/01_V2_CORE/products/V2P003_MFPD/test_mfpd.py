import unittest
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from mfpd import FidelityIdentificationChannel, identify_persistence_then_route_budget

REPO = HERE.parents[2]
FOUNDRY_PRODUCTS = REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products"
if str(FOUNDRY_PRODUCTS) not in sys.path:
    sys.path.insert(0, str(FOUNDRY_PRODUCTS))
from P144_DPAI.parents.dfdpe import simulate_affine_dynamics

FINE = FidelityIdentificationChannel("fine_identification", .0025, .005)
CHEAP = FidelityIdentificationChannel("cheap_identification", .01, .001)


def case(a, noise, seed, ntrain, *, rho=.9, total_budget=.1,
         fine=FINE, cheap=CHEAP):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 10, 101)
    u = np.sin(t) + .5 * np.cos(1.7 * t)
    y = simulate_affine_dynamics(t, u, 1, [a, .6, .05])
    obs = y + rng.normal(0, noise, len(t))
    return identify_persistence_then_route_budget(
        t[:ntrain], obs[:ntrain], u[:ntrain],
        window_duration=2, window_step=.5,
        total_budget=total_budget, fine_channel=fine, cheap_channel=cheap,
        pilot_correlation=rho,
    )


class P144InvariantPreservationTests(unittest.TestCase):
    def test_uncertain_boundary_case_still_acquires(self):
        r = case(-.03, .25, 2, 70)
        self.assertEqual(r.acquisition_family, "identification_experiment")
        self.assertGreater(max(r.fine_net_value, r.cheap_net_value), 0)

    def test_far_stable_case_still_skips(self):
        r = case(-.5, .05, 4, 90)
        self.assertEqual(r.mode, "no_measurement")
        self.assertIsNone(r.acquisition_family)

    def test_near_case_uncertainty_remains_material(self):
        self.assertGreater(case(-.03, .25, 2, 70).persistence_standard_error, .08)

    def test_far_case_remains_precise(self):
        self.assertLess(case(-.5, .05, 4, 90).persistence_standard_error, .02)

    def test_action_label_preserved(self):
        self.assertEqual(case(-.5, .05, 4, 90).current_action, "STABLE_SIDE")

    def test_status_contract_preserved(self):
        self.assertIn("PERSISTENCE", case(-.03, .25, 2, 70).status)


class K048ContrastiveCompositionTests(unittest.TestCase):
    def test_high_correlation_near_boundary_uses_multifidelity(self):
        r = case(-.03, .25, 2, 70, rho=.9)
        self.assertEqual(r.mode, "multifidelity")
        self.assertGreater(r.n_cheap, r.n_fine)

    def test_low_correlation_near_boundary_routes_fine_only(self):
        r = case(-.03, .25, 2, 70, rho=.01)
        self.assertEqual(r.mode, "fine_only")
        self.assertEqual(r.n_cheap, 0)

    def test_negative_value_cheap_channel_routes_fine_only(self):
        expensive_cheap = FidelityIdentificationChannel("cheap", .01, .05)
        r = case(-.03, .25, 2, 70, rho=.9, cheap=expensive_cheap)
        self.assertEqual(r.mode, "fine_only")
        self.assertEqual(r.n_cheap, 0)

    def test_budget_is_respected(self):
        r = case(-.03, .25, 2, 70, rho=.9, total_budget=.1)
        self.assertLessEqual(r.spent_budget, .1 + 1e-12)

    def test_multifidelity_proxy_improves_on_fine_only_baseline(self):
        multi = case(-.03, .25, 2, 70, rho=.9)
        fine = case(-.03, .25, 2, 70, rho=.01)
        self.assertEqual(multi.mode, "multifidelity")
        self.assertEqual(fine.mode, "fine_only")
        self.assertLess(multi.variance_proxy, fine.variance_proxy)

    def test_invalid_budget_contract_rejected(self):
        with self.assertRaises(ValueError):
            case(-.03, .25, 2, 70, total_budget=-1)


if __name__ == "__main__":
    unittest.main()
