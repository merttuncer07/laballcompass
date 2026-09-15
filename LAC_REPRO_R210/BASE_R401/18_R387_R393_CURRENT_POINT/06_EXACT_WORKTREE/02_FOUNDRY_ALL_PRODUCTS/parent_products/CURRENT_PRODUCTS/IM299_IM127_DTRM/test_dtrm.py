from __future__ import annotations

import unittest

from dtrm import DecisionTransientRiskMonitor, analyze_config, gronwall_decision_envelope


class DecisionTransientRiskMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.monitor = DecisionTransientRiskMonitor([[1, 0], [0, 1]], 0.1, 4.0, 4001)

    def test_relevant_direction_finds_flip(self) -> None:
        result = self.monitor.analyze_common_flow(
            [[-1, 20], [0, -2]], [1, 0], 0.2
        )
        self.assertAlmostEqual(result.directional_peak_gain, 5.025063, places=5)
        self.assertAlmostEqual(result.transient_action_flip_index, 2.512531, places=5)
        self.assertEqual(result.status, "ACTION_FLIP_DIRECTION_EXISTS")

    def test_irrelevant_direction_is_certified(self) -> None:
        result = self.monitor.analyze_common_flow(
            [[-1, 20], [0, -2]], [0, 1], 0.2
        )
        self.assertAlmostEqual(result.directional_peak_gain, 1.0, places=8)
        self.assertAlmostEqual(result.transient_action_flip_index, 0.5, places=8)
        self.assertEqual(result.status, "CERTIFIED_WITHIN_LINEAR_SHELL")

    def test_action_specific_flow_is_detected(self) -> None:
        result = self.monitor.analyze_action_branches(
            [[-1, 0], [0, -2]],
            [1, 0],
            [[-1, 20], [0, -2]],
            [1, 0],
            0.2,
        )
        self.assertAlmostEqual(result.directional_peak_gain, 5.0, places=5)
        self.assertAlmostEqual(result.transient_action_flip_index, 2.5, places=5)
        self.assertEqual(result.propagation_mode, "action_branch_difference")

    def test_config_interface(self) -> None:
        result = analyze_config(
            {
                "mode": "common_flow",
                "system_matrix": [[-1]],
                "uncertainty_map": [[1]],
                "uncertainty_radius": 0.1,
                "horizon": 1.0,
                "grid_points": 101,
                "decision_contrast": [1],
                "nominal_gap": 0.2,
            }
        )
        self.assertEqual(result["status"], "CERTIFIED_WITHIN_LINEAR_SHELL")

    def test_dimension_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.monitor.analyze_common_flow([[-1]], [1], 0.2)

    def test_zero_growth_envelope(self) -> None:
        result = gronwall_decision_envelope(0.1, 0.0, 0.02, 5.0, 1.0, 0.5)
        self.assertAlmostEqual(result.peak_state_error_bound, 0.2)
        self.assertEqual(result.status, "ENVELOPE_CERTIFIES_ACTION")

    def test_positive_growth_can_expose_decision_risk(self) -> None:
        result = gronwall_decision_envelope(0.05, 0.4, 0.02, 5.0, 3.0, 0.5)
        self.assertGreater(result.action_flip_index_bound, 1.0)


if __name__ == "__main__":
    unittest.main()
