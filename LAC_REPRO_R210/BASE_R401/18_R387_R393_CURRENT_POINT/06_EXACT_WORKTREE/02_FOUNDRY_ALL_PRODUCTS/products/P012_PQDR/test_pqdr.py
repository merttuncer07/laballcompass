import unittest

import numpy as np

if __package__:
    from .pqdr import PersistenceQualifiedDecisionRiskMonitor
else:
    from pqdr import PersistenceQualifiedDecisionRiskMonitor


def monitor() -> PersistenceQualifiedDecisionRiskMonitor:
    return PersistenceQualifiedDecisionRiskMonitor(
        uncertainty_map=np.eye(2),
        uncertainty_radius=0.5,
        horizon=2.0,
        sample_interval=1.0,
        minimum_exposure=0.1,
        minimum_recovery_steps=10,
        recovery_floor=0.05,
        scalar_alarm_distance=10.0,
        grid_points=101,
    )


class PQDRTests(unittest.TestCase):
    def test_slow_flip_is_persistence_qualified(self):
        result = monitor().analyze_common_flow(
            system_generator=np.diag([-0.02, -0.02]),
            decision_contrast=[1.0, -1.0],
            nominal_gap=0.4,
        )
        self.assertTrue(result.action_flip_possible)
        self.assertTrue(result.persistent_decision_mode)
        self.assertEqual(result.status, "PERSISTENT_ACTION_FLIP_RISK")

    def test_fast_flip_remains_transient(self):
        result = monitor().analyze_common_flow(
            system_generator=np.diag([-2.0, -2.0]),
            decision_contrast=[1.0, -1.0],
            nominal_gap=0.4,
        )
        self.assertTrue(result.action_flip_possible)
        self.assertFalse(result.persistent_decision_mode)
        self.assertEqual(result.status, "TRANSIENT_ACTION_FLIP_RISK")

    def test_large_gap_is_certified(self):
        result = monitor().analyze_common_flow(
            system_generator=np.diag([-0.02, -0.02]),
            decision_contrast=[1.0, -1.0],
            nominal_gap=5.0,
        )
        self.assertFalse(result.action_flip_possible)

    def test_dimension_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            monitor().analyze_common_flow(
                system_generator=np.eye(3),
                decision_contrast=[1.0, 0.0, -1.0],
                nominal_gap=0.4,
            )


if __name__ == "__main__":
    unittest.main()
