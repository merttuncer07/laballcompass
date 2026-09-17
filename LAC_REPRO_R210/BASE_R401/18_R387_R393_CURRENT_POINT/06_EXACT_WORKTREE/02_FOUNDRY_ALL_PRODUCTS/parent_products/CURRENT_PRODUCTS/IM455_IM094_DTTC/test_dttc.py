from __future__ import annotations

import json
import unittest

import numpy as np

from dttc import DecisionTargetedTriggerDesigner, TriggerCandidate, design_from_config


class DecisionTargetedTriggerDesignerTests(unittest.TestCase):
    def test_coarse_signal_can_beat_high_correlation_signal(self) -> None:
        loss = np.array([0, 1, 2, 3, 100], dtype=float)
        probability = np.array([40, 30, 20, 9, 1])
        expanded_loss = np.repeat(loss, probability)
        event = expanded_loss > 2.5
        high_corr = np.repeat(np.array([0, 1, 2, 2, 100], dtype=float), probability)
        coarse = np.repeat(np.array([0, 0, 0, 1, 1], dtype=float), probability)
        designer = DecisionTargetedTriggerDesigner(5.0, 1.0, threshold_grid_size=101)
        result = designer.design(
            [TriggerCandidate("high_corr"), TriggerCandidate("coarse")],
            {"high_corr": high_corr, "coarse": coarse},
            event,
            expanded_loss,
        )
        self.assertEqual(result["selected"]["candidate"], "coarse")

    def test_manipulation_cost_changes_channel_choice(self) -> None:
        loss = np.array([0, 0, 0, 2, 2, 2], dtype=float)
        event = loss > 1
        signals = {"local": loss.copy(), "regional": loss.copy()}
        designer = DecisionTargetedTriggerDesigner(5.0, 1.0)
        result = designer.design(
            [
                TriggerCandidate("local", manipulation_exposure=1.0),
                TriggerCandidate("regional", verification_cost=0.1),
            ],
            signals,
            event,
            loss,
        )
        self.assertEqual(result["selected"]["candidate"], "regional")

    def test_config_interface(self) -> None:
        config = {
            "loss_column": "loss",
            "protected_loss_threshold": 1.0,
            "false_negative_cost": 5.0,
            "false_positive_cost": 1.0,
            "candidates": [{"column": "index"}],
        }
        result = design_from_config(config, {"loss": [0, 2, 3], "index": [0, 1, 1]})
        self.assertEqual(result["selected"]["candidate"], "index")

    def test_constant_vector_has_explicit_undefined_correlation_and_strict_json(self) -> None:
        designer = DecisionTargetedTriggerDesigner(1.0, 1.0)
        result = designer.fit_candidate(
            TriggerCandidate("constant-loss"), [1, 2, 3], [False, True, False], [1, 1, 1]
        ).as_dict()
        self.assertIsNone(result["correlation_with_loss"])
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
