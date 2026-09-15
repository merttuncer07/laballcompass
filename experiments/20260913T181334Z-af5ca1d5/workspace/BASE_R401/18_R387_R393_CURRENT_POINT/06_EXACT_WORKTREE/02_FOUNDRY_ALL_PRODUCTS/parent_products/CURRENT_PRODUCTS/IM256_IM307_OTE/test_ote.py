from __future__ import annotations

import unittest

import numpy as np

from ote import OrthogonalTargetEstimator, estimate_from_nuisance_predictions


class OrthogonalTargetEstimatorTests(unittest.TestCase):
    def test_recovers_linear_target_with_confounding(self) -> None:
        rng = np.random.default_rng(1)
        x = rng.normal(size=(5000, 2))
        d = x @ np.array([1.0, -0.5]) + rng.normal(size=5000)
        y = 1.5 * d + x @ np.array([0.8, 0.4]) + rng.normal(size=5000)
        result = OrthogonalTargetEstimator(folds=5, seed=2).fit(x, d, y)
        self.assertLess(abs(result.target - 1.5), 0.08)

    def test_zero_residual_treatment_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            estimate_from_nuisance_predictions([1, 1], [2, 2], [1, 1], [2, 2])

    def test_confidence_interval_is_ordered(self) -> None:
        result = estimate_from_nuisance_predictions(
            [0, 1, 2, 3], [0, 2, 4, 6], [0, 0, 0, 0], [0, 0, 0, 0]
        )
        self.assertLessEqual(result.confidence_low_95, result.target)
        self.assertGreaterEqual(result.confidence_high_95, result.target)


if __name__ == "__main__":
    unittest.main()
