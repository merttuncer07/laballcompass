import unittest

import numpy as np

from utdim import monitor_double_diffusive_instability


class Tests(unittest.TestCase):
    def test_rate_mismatch_destabilizes_statically_stable_gradient(self):
        result = monitor_double_diffusive_instability(
            viscosity=.1, diffusivities=[1, .01], buoyancy_coefficients=[1, 1],
            background_gradients=[2, -1], wavenumbers=np.logspace(-2, 2, 200),
        )
        self.assertGreater(result.static_stability_index, 0)
        self.assertGreater(result.maximum_growth_rate, 0)
        self.assertLess(result.equal_transport_growth_at_fastest_mode, 0)
        self.assertEqual(result.status, "UNEQUAL_TRANSPORT_DESTABILIZATION_DETECTED")

    def test_equal_diffusivities_do_not_create_mismatch_claim(self):
        result = monitor_double_diffusive_instability(
            viscosity=.1, diffusivities=[.5, .5], buoyancy_coefficients=[1, 1],
            background_gradients=[2, -1], wavenumbers=np.logspace(-2, 2, 100),
        )
        self.assertNotEqual(result.status, "UNEQUAL_TRANSPORT_DESTABILIZATION_DETECTED")

    def test_statically_unstable_case_is_not_misattributed(self):
        result = monitor_double_diffusive_instability(
            viscosity=.1, diffusivities=[1, .01], buoyancy_coefficients=[1, 1],
            background_gradients=[-1, -1], wavenumbers=np.logspace(-2, 2, 100),
        )
        self.assertLess(result.static_stability_index, 0)
        self.assertEqual(result.status, "INSTABILITY_NOT_UNIQUELY_ATTRIBUTABLE_TO_TRANSPORT_MISMATCH")

    def test_unsorted_wavenumbers_are_rejected(self):
        with self.assertRaises(ValueError):
            monitor_double_diffusive_instability(
                viscosity=1, diffusivities=[1, 2], buoyancy_coefficients=[1, 1],
                background_gradients=[1, 1], wavenumbers=[1, .5],
            )


if __name__ == "__main__":
    unittest.main()
