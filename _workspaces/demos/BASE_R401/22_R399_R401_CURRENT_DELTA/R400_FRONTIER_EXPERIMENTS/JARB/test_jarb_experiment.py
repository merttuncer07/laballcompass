import unittest

import numpy as np

from jarb_experiment import actual_joint_loss, candidate, choose, removal_control


H = np.asarray(
    [
        [0.46, 0.69, 0.05],
        [0.03, 0.85, 0.59],
        [0.31, 0.32, 0.09],
        [0.17, 0.02, 0.84],
    ]
)
DECLARED = [8.0, 3.0, 1.0]


class JARBExperimentTests(unittest.TestCase):
    def test_interaction_changes_joint_decision(self):
        self.assertNotEqual(candidate(DECLARED, H, 5).sensors, removal_control(DECLARED, H, 5).sensors)

    def test_candidate_improves_declared_joint_loss(self):
        proposed = candidate(DECLARED, H, 5)
        control = removal_control(DECLARED, H, 5)
        self.assertLess(proposed.declared_joint_loss, control.declared_joint_loss)

    def test_same_budget_and_feasible_options(self):
        proposed = candidate(DECLARED, H, 5)
        control = removal_control(DECLARED, H, 5)
        self.assertLessEqual(proposed.spent_budget, 5)
        self.assertLessEqual(control.spent_budget, 5)

    def test_zero_coupling_is_exact_removal_control(self):
        self.assertEqual(choose(DECLARED, H, 5, coupling=0.0), removal_control(DECLARED, H, 5))

    def test_minimum_budget_collapses_exactly(self):
        self.assertEqual(candidate(DECLARED, H, 4), removal_control(DECLARED, H, 4))

    def test_maximum_budget_collapses_exactly(self):
        self.assertEqual(candidate(DECLARED, H, 13), removal_control(DECLARED, H, 13))

    def test_wrong_consequence_can_hurt(self):
        proposed = candidate(DECLARED, H, 5)
        control = removal_control(DECLARED, H, 5)
        truth = [20.0, 1.0, 1.0]
        self.assertGreater(actual_joint_loss(proposed, H, truth), actual_joint_loss(control, H, truth))

    def test_decision_is_deterministic(self):
        self.assertEqual(candidate(DECLARED, H, 5), candidate(DECLARED, H, 5))

    def test_consequence_alignment_required(self):
        with self.assertRaises(ValueError):
            candidate([1.0, 2.0], H, 5)

    def test_negative_consequence_rejected(self):
        with self.assertRaises(ValueError):
            candidate([1.0, -1.0, 2.0], H, 5)

    def test_nonfinite_sensor_rejected(self):
        broken = H.copy()
        broken[0, 0] = np.nan
        with self.assertRaises(ValueError):
            candidate(DECLARED, broken, 5)

    def test_out_of_range_budget_rejected(self):
        with self.assertRaises(ValueError):
            candidate(DECLARED, H, 3)

    def test_out_of_range_coupling_rejected(self):
        with self.assertRaises(ValueError):
            choose(DECLARED, H, 5, coupling=1.1)


if __name__ == "__main__":
    unittest.main()
