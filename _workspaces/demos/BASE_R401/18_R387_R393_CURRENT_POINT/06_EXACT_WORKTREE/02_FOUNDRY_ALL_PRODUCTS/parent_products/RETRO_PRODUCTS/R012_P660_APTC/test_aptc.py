import unittest

import numpy as np

from aptc import calculate_ambipolar_transport


class Tests(unittest.TestCase):
    def test_neutral_limit_matches_ambipolar_formula(self):
        x = np.linspace(-3, 3, 101); density = .01 + np.exp(-x*x)
        result = calculate_ambipolar_transport(
            x, density, density, electron_mobility=4, hole_mobility=1,
            electron_diffusivity=10, hole_diffusivity=2,
        )
        self.assertAlmostEqual(result.ambipolar_diffusion_coefficient_neutral_limit, 3.6)
        self.assertEqual(result.status, "AMBIPOLAR_PACKET_TRANSPORT_VALID")

    def test_internal_field_cancels_flux_separation(self):
        x = np.linspace(-3, 3, 101); density = .01 + np.exp(-x*x)
        result = calculate_ambipolar_transport(
            x, density, density, electron_mobility=4, hole_mobility=1,
            electron_diffusivity=10, hole_diffusivity=2,
        )
        self.assertLess(result.maximum_coupled_flux_mismatch, 1e-10)
        self.assertGreater(result.maximum_uncoupled_flux_mismatch, 1)

    def test_non_neutral_profile_is_flagged(self):
        x = np.linspace(-2, 2, 51); n = np.ones(51); p = np.full(51, .7)
        result = calculate_ambipolar_transport(
            x, n, p, electron_mobility=2, hole_mobility=1,
            electron_diffusivity=3, hole_diffusivity=1,
        )
        self.assertEqual(result.status, "QUASINEUTRAL_PACKET_ASSUMPTION_EXCEEDED")

    def test_forecast_spread_increases(self):
        x = np.linspace(-3, 3, 101); density = .01 + np.exp(-x*x)
        result = calculate_ambipolar_transport(
            x, density, density, electron_mobility=2, hole_mobility=1,
            electron_diffusivity=3, hole_diffusivity=1, forecast_time=2,
        )
        self.assertGreater(result.predicted_packet_variance, result.initial_packet_variance)


if __name__ == "__main__":
    unittest.main()
