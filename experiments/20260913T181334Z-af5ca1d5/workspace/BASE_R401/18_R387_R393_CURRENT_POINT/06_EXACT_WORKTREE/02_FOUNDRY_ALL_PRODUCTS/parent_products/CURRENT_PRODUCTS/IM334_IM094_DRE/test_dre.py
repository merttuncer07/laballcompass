from __future__ import annotations

import unittest

from dre import DecisionRelevantExplorer, GaussianArm


class DecisionRelevantExplorerTests(unittest.TestCase):
    def test_far_below_high_variance_arm_is_not_automatically_selected(self) -> None:
        arms = [
            GaussianArm("best", 1.0, 0.05, 1.0),
            GaussianArm("near", 0.9, 0.10, 1.0),
            GaussianArm("far", -5.0, 5.0, 1.0),
        ]
        self.assertNotEqual(DecisionRelevantExplorer().choose(arms, 50), "far")

    def test_near_contender_gains_information_value(self) -> None:
        arms = [GaussianArm("a", 1.0, 0.04, 1.0), GaussianArm("b", 0.95, 0.09, 1.0)]
        scores = {item.arm: item for item in DecisionRelevantExplorer().score(arms, 80)}
        self.assertGreater(scores["b"].future_information_value, 0)

    def test_posterior_variance_decreases_after_observation(self) -> None:
        arm = GaussianArm("a", 0.0, 1.0, 1.0)
        self.assertLess(arm.update(1.0).variance, arm.variance)


if __name__ == "__main__":
    unittest.main()
