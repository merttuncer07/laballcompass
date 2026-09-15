import unittest

from wbdp import Distribution, displacement_interpolation, wasserstein_barycenter, wasserstein_distance


class WBDPTests(unittest.TestCase):
    def test_point_mass_interpolation_moves_mass(self):
        a, b = Distribution("a", (0,), (1,)), Distribution("b", (10,), (1,))
        result = displacement_interpolation(a, b, 0.5)
        self.assertEqual(result.positions, (5.0,)); self.assertEqual(result.variance, 0.0)

    def test_path_distance_is_linear_in_fraction(self):
        a = Distribution("a", (0, 2), (0.5, 0.5)); b = Distribution("b", (8, 10), (0.5, 0.5))
        result = displacement_interpolation(a, b, 0.25); total = wasserstein_distance(a, b)
        self.assertAlmostEqual(result.source_wasserstein_distances["a"], 0.25 * total)
        self.assertAlmostEqual(result.source_wasserstein_distances["b"], 0.75 * total)

    def test_equal_weight_point_barycenter_is_midpoint(self):
        result = wasserstein_barycenter(
            [Distribution("a", (0,), (1,)), Distribution("b", (10,), (1,))]
        )
        self.assertEqual(result.positions, (5.0,))
        self.assertAlmostEqual(result.weighted_squared_transport_objective, 25.0)

    def test_invalid_mass_is_rejected(self):
        with self.assertRaises(ValueError):
            wasserstein_barycenter([Distribution("bad", (0, 1), (0, 0))])


if __name__ == "__main__": unittest.main()
