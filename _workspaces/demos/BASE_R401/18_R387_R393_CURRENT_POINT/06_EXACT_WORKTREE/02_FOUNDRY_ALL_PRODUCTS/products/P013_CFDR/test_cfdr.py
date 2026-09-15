import unittest

import numpy as np

if __package__:
    from .cfdr import ConservationFeasibleDecisionRiskMonitor
else:
    from cfdr import ConservationFeasibleDecisionRiskMonitor
if __package__:
    from .parents.ccvc import ConservationConstrainedViability
else:
    from parents.ccvc import ConservationConstrainedViability


def viability(rate: float = 0.02) -> ConservationConstrainedViability:
    return ConservationConstrainedViability(
        drift_matrix=-rate * np.eye(2),
        control_matrix=np.array([[1.0], [-1.0]]),
        conservation_matrix=np.array([[1.0, 1.0]]),
        conservation_value=np.array([0.0]),
        safe_matrix=np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]]),
        safe_bound=np.ones(4),
        control_lower=np.array([-1.0]),
        control_upper=np.array([1.0]),
    )


def monitor() -> ConservationFeasibleDecisionRiskMonitor:
    return ConservationFeasibleDecisionRiskMonitor(
        viability_model=viability(),
        uncertainty_map=np.eye(2),
        uncertainty_radius=0.5,
        horizon=2.0,
        grid_points=101,
    )


class CFDRTests(unittest.TestCase):
    def test_conservation_removes_normal_flip(self):
        result = monitor().analyze_common_flow(
            system_matrix=-0.02 * np.eye(2),
            decision_contrast=[1.0, 1.0],
            nominal_gap=0.4,
            nominal_state=[0.0, 0.0],
        )
        self.assertEqual(result.status, "CONSERVATION_REMOVES_RAW_ACTION_FLIP")
        self.assertEqual(result.feasible_latent_dimension, 1)
        self.assertLess(result.conservation_residual_of_worst_feasible_perturbation, 1e-10)

    def test_tangent_flip_survives(self):
        result = monitor().analyze_common_flow(
            system_matrix=-0.02 * np.eye(2),
            decision_contrast=[1.0, -1.0],
            nominal_gap=0.4,
            nominal_state=[0.0, 0.0],
        )
        self.assertEqual(result.status, "CONSERVATION_FEASIBLE_ACTION_FLIP")
        self.assertTrue(result.worst_feasible_state_in_safe_set)

    def test_optional_control_filter_is_applied(self):
        result = monitor().analyze_common_flow(
            system_matrix=-0.02 * np.eye(2),
            decision_contrast=[1.0, -1.0],
            nominal_gap=0.4,
            nominal_state=[0.0, 0.0],
            nominal_control=[1.0],
            safety_step=0.1,
        )
        self.assertIsNotNone(result.filtered_control)

    def test_dynamics_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            monitor().analyze_common_flow(
                system_matrix=-0.03 * np.eye(2),
                decision_contrast=[1.0, -1.0],
                nominal_gap=0.4,
                nominal_state=[0.0, 0.0],
            )


if __name__ == "__main__":
    unittest.main()
