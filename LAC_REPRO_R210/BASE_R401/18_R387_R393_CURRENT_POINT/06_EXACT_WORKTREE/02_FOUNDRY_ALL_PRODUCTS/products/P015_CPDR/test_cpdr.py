import unittest

import numpy as np

if __package__:
    from .cfdr import ConservationFeasibleDecisionRiskMonitor
else:
    from cfdr import ConservationFeasibleDecisionRiskMonitor
if __package__:
    from .cpdr import ConservationPersistenceDecisionRiskMonitor
else:
    from cpdr import ConservationPersistenceDecisionRiskMonitor
if __package__:
    from .parents.ccvc import ConservationConstrainedViability
else:
    from parents.ccvc import ConservationConstrainedViability


def build(rate: float) -> ConservationPersistenceDecisionRiskMonitor:
    viability = ConservationConstrainedViability(
        drift_matrix=-rate * np.eye(2),
        control_matrix=np.array([[1.0], [-1.0]]),
        conservation_matrix=np.array([[1.0, 1.0]]),
        conservation_value=np.array([0.0]),
        safe_matrix=np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]]),
        safe_bound=np.ones(4),
        control_lower=np.array([-1.0]),
        control_upper=np.array([1.0]),
    )
    cfdr = ConservationFeasibleDecisionRiskMonitor(
        viability_model=viability,
        uncertainty_map=np.eye(2),
        uncertainty_radius=0.5,
        horizon=2.0,
        grid_points=101,
    )
    return ConservationPersistenceDecisionRiskMonitor(
        conservation_monitor=cfdr,
        sample_interval=1.0,
        minimum_exposure=0.1,
        minimum_recovery_steps=10,
        recovery_floor=0.05,
        scalar_alarm_distance=10.0,
    )


class CPDRTests(unittest.TestCase):
    def test_normal_flip_is_removed_by_conservation(self):
        result = build(0.02).analyze_common_flow(
            system_generator=-0.02 * np.eye(2),
            decision_contrast=[1.0, 1.0],
            nominal_gap=0.4,
            nominal_state=[0.0, 0.0],
        )
        self.assertEqual(result.status, "RAW_ACTION_FLIP_PHYSICALLY_INFEASIBLE")
        self.assertFalse(result.action_flip_feasible)

    def test_slow_tangent_flip_is_persistent(self):
        result = build(0.02).analyze_common_flow(
            system_generator=-0.02 * np.eye(2),
            decision_contrast=[1.0, -1.0],
            nominal_gap=0.4,
            nominal_state=[0.0, 0.0],
        )
        self.assertEqual(result.status, "PERSISTENT_FEASIBLE_ACTION_FLIP_RISK")
        self.assertTrue(result.persistent_decision_mode)

    def test_fast_tangent_flip_is_transient(self):
        result = build(2.0).analyze_common_flow(
            system_generator=-2.0 * np.eye(2),
            decision_contrast=[1.0, -1.0],
            nominal_gap=0.4,
            nominal_state=[0.0, 0.0],
        )
        self.assertEqual(result.status, "TRANSIENT_FEASIBLE_ACTION_FLIP_RISK")
        self.assertFalse(result.persistent_decision_mode)

    def test_control_filter_is_preserved(self):
        result = build(0.02).analyze_common_flow(
            system_generator=-0.02 * np.eye(2),
            decision_contrast=[1.0, -1.0],
            nominal_gap=0.4,
            nominal_state=[0.0, 0.0],
            nominal_control=[1.0],
            safety_step=0.1,
        )
        self.assertIsNotNone(result.conservation_risk.filtered_control)


if __name__ == "__main__":
    unittest.main()
