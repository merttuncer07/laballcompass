import unittest

import numpy as np

from csdc import simulate_curvature_coarsening


class Tests(unittest.TestCase):
    def test_small_particles_dissolve_and_mean_size_grows(self):
        radii = np.linspace(.4, 1.6, 100)
        result = simulate_curvature_coarsening(radii, mobility=.03, maximum_time=20, time_step=.01)
        self.assertGreater(result.dissolved_particle_count, 0)
        self.assertGreater(result.final_mean_radius, result.initial_mean_radius)

    def test_material_volume_is_preserved(self):
        radii = np.linspace(.5, 1.5, 80)
        result = simulate_curvature_coarsening(radii, mobility=.02, maximum_time=5, time_step=.005)
        self.assertAlmostEqual(sum(r ** 3 for r in result.initial_radii), sum(r ** 3 for r in result.final_radii), places=8)

    def test_controller_stops_at_requested_mean(self):
        radii = np.linspace(.4, 1.6, 120)
        result = simulate_curvature_coarsening(radii, mobility=.04, maximum_time=40, time_step=.005, target_mean_radius=1.2)
        self.assertEqual(result.status, "TARGET_MEAN_RADIUS_REACHED")
        self.assertGreaterEqual(result.final_mean_radius, 1.2)
        self.assertLess(result.stop_time, 40)

    def test_nonpositive_radius_is_rejected(self):
        with self.assertRaises(ValueError):
            simulate_curvature_coarsening([1, 0], mobility=1, maximum_time=1, time_step=.1)


if __name__ == "__main__":
    unittest.main()
