import unittest

import numpy as np

from tdsx import confounding_e_value, explore_sensitivity_surface, missing_mean_tipping_value


class TDSXTests(unittest.TestCase):
    def test_nearest_tipping_point_is_found(self) -> None:
        result = explore_sensitivity_surface(
            lambda p: 1.0 - p["x"] - p["y"],
            {"x": np.linspace(0, 1, 11), "y": np.linspace(0, 1, 11)},
            {"x": 0.0, "y": 0.0}, decision_threshold=0.0,
        )
        self.assertEqual(result.status, "TIPPING_POINT_FOUND")
        self.assertIsNotNone(result.tipping_point)

    def test_no_flip_is_reported_without_inventing_one(self) -> None:
        result = explore_sensitivity_surface(
            lambda p: 5.0 + p["x"], {"x": [0, 1]}, {"x": 0}, decision_threshold=0,
        )
        self.assertEqual(result.status, "NO_FLIP_INSIDE_DECLARED_SURFACE")
        self.assertIsNone(result.tipping_point)

    def test_missing_mean_tipping_is_exact(self) -> None:
        value = missing_mean_tipping_value([8, 10, 12, 14], 2, 9.0)
        self.assertAlmostEqual((44 + 2 * value) / 6, 9.0)

    def test_e_value_matches_risk_ratio_formula(self) -> None:
        self.assertAlmostEqual(confounding_e_value(2.0), 2 + np.sqrt(2))
        self.assertAlmostEqual(confounding_e_value(0.5), 2 + np.sqrt(2))


if __name__ == "__main__":
    unittest.main()
