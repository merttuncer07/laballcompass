import unittest

import numpy as np

from jarb_native import (
    actual_joint_loss,
    candidate,
    choose,
    observability_select,
    removal_control,
    representation_candidate,
)


DECLARED = [0.24978747391615905, 0.22466954832223132, 2.147769467852834]
H = np.asarray(
    [
        [0.04, 0.73, 0.59],
        [0.86, 0.19, 0.76],
        [0.75, 0.21, 0.43],
        [0.46, 0.52, 0.35],
        [0.22, 0.59, 0.20],
    ]
)


class NativeJARBTests(unittest.TestCase):
    def test_coupling_changes_native_budget_split(self):
        self.assertNotEqual(candidate(DECLARED, H, 9).sensor_budget, removal_control(DECLARED, H, 9).sensor_budget)

    def test_candidate_improves_declared_joint_loss(self):
        self.assertLess(candidate(DECLARED, H, 9).declared_joint_loss, removal_control(DECLARED, H, 9).declared_joint_loss)

    def test_candidate_uses_exact_reoc_decision(self):
        decision = candidate(DECLARED, H, 9)
        self.assertEqual(decision.sensors, observability_select(DECLARED, H, decision.sensor_budget).sensors)

    def test_candidate_uses_exact_cadsbc_decision(self):
        decision = candidate(DECLARED, H, 9)
        self.assertEqual(decision.modes, representation_candidate(DECLARED, decision.representation_budget).modes)

    def test_budget_is_preserved_exactly(self):
        for decision in (candidate(DECLARED, H, 9), removal_control(DECLARED, H, 9)):
            self.assertEqual(decision.sensor_budget + decision.representation_budget, 9)

    def test_zero_coupling_is_exact_control(self):
        self.assertEqual(choose(DECLARED, H, 9, coupling=0.0), removal_control(DECLARED, H, 9))

    def test_minimum_budget_collapses_exactly(self):
        self.assertEqual(candidate(DECLARED, H, 4), removal_control(DECLARED, H, 4))

    def test_maximum_budget_collapses_exactly(self):
        self.assertEqual(candidate(DECLARED, H, 14), removal_control(DECLARED, H, 14))

    def test_miscalibrated_consequence_can_hurt(self):
        proposed = candidate(DECLARED, H, 9)
        control = removal_control(DECLARED, H, 9)
        truth = [1.0, 1.0, 20.0]
        self.assertGreater(actual_joint_loss(proposed, H, truth), actual_joint_loss(control, H, truth))

    def test_decision_is_deterministic(self):
        self.assertEqual(candidate(DECLARED, H, 9), candidate(DECLARED, H, 9))

    def test_alignment_required(self):
        with self.assertRaises(ValueError):
            candidate([1.0, 2.0], H, 9)

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            candidate(DECLARED, H, 3)

    def test_invalid_coupling_rejected(self):
        with self.assertRaises(ValueError):
            choose(DECLARED, H, 9, coupling=-0.1)


if __name__ == "__main__":
    unittest.main()
