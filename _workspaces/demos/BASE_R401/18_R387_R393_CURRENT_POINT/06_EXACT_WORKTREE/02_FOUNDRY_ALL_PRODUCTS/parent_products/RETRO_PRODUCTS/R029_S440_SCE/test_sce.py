import unittest

import numpy as np

from sce import run_specification_curve


class SCETests(unittest.TestCase):
    def test_exact_linear_effect_is_recovered(self) -> None:
        x = np.linspace(-2, 2, 200)
        y = 3.0 * x + 2.0
        curve = run_specification_curve(
            outcomes={"y": y}, treatments={"x": x}, controls={}, control_sets={"none": []},
            samples={"all": np.ones(x.size, dtype=bool)},
        )
        self.assertAlmostEqual(curve.results[0].estimate, 3.0, places=10)

    def test_declared_choice_cross_product_is_complete(self) -> None:
        x = np.arange(20, dtype=float)
        curve = run_specification_curve(
            outcomes={"a": x, "b": x + 1}, treatments={"x": x}, controls={"z": x**2},
            control_sets={"none": [], "z": ["z"]},
            samples={"all": np.ones(20, dtype=bool), "late": x > 5},
        )
        self.assertEqual(len(curve.results), 8)

    def test_confounding_changes_magnitude(self) -> None:
        rng = np.random.default_rng(29)
        z = rng.normal(size=5_000)
        x = z + rng.normal(size=5_000)
        y = 0.5 * x + 2.0 * z + rng.normal(size=5_000)
        curve = run_specification_curve(
            outcomes={"y": y}, treatments={"x": x}, controls={"z": z},
            control_sets={"none": [], "adjusted": ["z"]}, samples={"all": np.ones(x.size, dtype=bool)},
        )
        estimates = {item.control_set: item.estimate for item in curve.results}
        self.assertGreater(estimates["none"] - estimates["adjusted"], 0.8)

    def test_rank_deficiency_is_visible_not_silently_dropped(self) -> None:
        x = np.arange(30, dtype=float)
        curve = run_specification_curve(
            outcomes={"y": 2 * x}, treatments={"x": x}, controls={"duplicate": x},
            control_sets={"bad": ["duplicate"]}, samples={"all": np.ones(x.size, dtype=bool)},
        )
        self.assertEqual(curve.invalid_specifications, 1)
        self.assertEqual(curve.results[0].status, "INSUFFICIENT_OR_RANK_DEFICIENT")


if __name__ == "__main__":
    unittest.main()
