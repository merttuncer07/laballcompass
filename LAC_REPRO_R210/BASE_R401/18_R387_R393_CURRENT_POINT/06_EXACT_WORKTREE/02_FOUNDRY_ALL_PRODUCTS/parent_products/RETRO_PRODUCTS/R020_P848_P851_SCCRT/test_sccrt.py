import unittest

import numpy as np

from sccrt import design_regeneration_capacity, simulate_catalyst_cycle


class Tests(unittest.TestCase):
    def test_no_regeneration_depletes_state_and_passive_model_overpredicts(self):
        result = simulate_catalyst_cycle(
            np.ones(200), np.zeros(200), time_step=.02,
            reaction_rate_constant=.5, regeneration_rate_constant=.5,
            catalyst_lattice_capacity=100,
        )
        self.assertLess(result.final_active_fraction, .2)
        self.assertGreater(result.passive_overprediction_fraction, 0)
        self.assertEqual(result.status, "REGENERATION_CAPACITY_INSUFFICIENT")

    def test_material_balance_closes(self):
        result = simulate_catalyst_cycle(
            [1, 0] * 100, [0, 1] * 100, time_step=.01,
            reaction_rate_constant=.3, regeneration_rate_constant=.4,
            catalyst_lattice_capacity=50,
        )
        self.assertAlmostEqual(result.material_balance_error, 0, places=10)

    def test_capacity_designer_chooses_smallest_feasible_scale(self):
        reactant = np.tile(np.r_[np.ones(50), np.zeros(50)], 4)
        oxidant = np.tile(np.r_[np.zeros(50), np.ones(50)], 4)
        result = design_regeneration_capacity(
            reactant, oxidant, [.25, .5, 1, 2, 4],
            required_minimum_active_fraction=.2, required_final_active_fraction=.8,
            time_step=.02, reaction_rate_constant=.3, regeneration_rate_constant=.3,
            catalyst_lattice_capacity=100,
        )
        self.assertTrue(result.feasible)
        lower = [r for scale, r in result.candidates if scale < result.selected_oxidant_scale]
        self.assertTrue(all(r.final_active_fraction < .8 or r.minimum_active_fraction < .2 for r in lower))

    def test_impossible_scaled_rates_are_not_silently_clipped(self):
        with self.assertRaises(ValueError):
            design_regeneration_capacity(
                [1, 0], [0, 1], [-1, 1], required_minimum_active_fraction=.2,
                required_final_active_fraction=.8, time_step=.1,
                reaction_rate_constant=.2, regeneration_rate_constant=.2,
                catalyst_lattice_capacity=1,
            )


if __name__ == "__main__":
    unittest.main()
