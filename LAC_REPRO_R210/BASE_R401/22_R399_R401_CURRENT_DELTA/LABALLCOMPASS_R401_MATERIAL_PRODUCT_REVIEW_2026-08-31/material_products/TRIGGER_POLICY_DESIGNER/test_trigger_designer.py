from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from trigger_designer import Candidate, TriggerPolicyDesigner, design_from_files, main


class TriggerPolicyDesignerTests(unittest.TestCase):
    def test_high_direction_finds_separating_threshold(self) -> None:
        designer = TriggerPolicyDesigner(10, 1)
        threshold, metrics = designer.fit(
            Candidate("signal", "high"), [1, 2, 3, 8, 9], [False, False, False, True, True]
        )
        self.assertGreaterEqual(threshold, 3)
        self.assertEqual(metrics.false_negatives, 0)
        self.assertEqual(metrics.false_positives, 0)

    def test_low_direction_is_supported(self) -> None:
        designer = TriggerPolicyDesigner(10, 1)
        threshold, metrics = designer.fit(
            Candidate("health", "low"), [9, 8, 7, 2, 1], [False, False, False, True, True]
        )
        self.assertLessEqual(threshold, 7)
        self.assertEqual(metrics.false_negatives, 0)
        self.assertEqual(metrics.false_positives, 0)

    def test_verification_cost_can_prefer_fewer_triggers(self) -> None:
        designer = TriggerPolicyDesigner(3, 1)
        threshold, metrics = designer.fit(
            Candidate("signal", "high", verification_cost_per_trigger=10),
            [1, 2, 3, 4],
            [False, False, True, True],
        )
        self.assertEqual(metrics.triggers, 0)

    def test_selection_uses_calibration_not_evaluation(self) -> None:
        root = Path(__file__).parent
        result = design_from_files(
            json.loads((root / "example_config.json").read_text(encoding="utf-8")),
            root / "example_machine_history.csv",
        )
        calibration_costs = {
            row["candidate"]["column"]: row["calibration"]["average_cost_per_row"]
            for row in result["candidate_results"]
        }
        selected = result["selected"]["candidate"]["column"]
        self.assertEqual(calibration_costs[selected], min(calibration_costs.values()))
        self.assertEqual(result["partition"]["evaluation_rows"], 10)

    def test_small_partitions_are_rejected(self) -> None:
        config = {
            "loss_column": "loss",
            "protected_loss_threshold": 1,
            "false_negative_cost": 1,
            "false_positive_cost": 1,
            "candidates": [{"column": "x"}],
        }
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "tiny.csv"
            with data.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["x", "loss"])
                writer.writeheader()
                writer.writerows([{"x": 1, "loss": 0}, {"x": 2, "loss": 2}, {"x": 3, "loss": 0}])
            with self.assertRaisesRegex(ValueError, "each require at least two rows"):
                design_from_files(config, data)

    def test_cli_writes_artifacts(self) -> None:
        root = Path(__file__).parent
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "policy.json"
            report = Path(temp) / "policy.md"
            code = main(
                [
                    str(root / "example_config.json"),
                    str(root / "example_machine_history.csv"),
                    "--output",
                    str(output),
                    "--report",
                    str(report),
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["product"], "TRIGGER_POLICY_DESIGNER_V1")
            self.assertIn("Holdout performance", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
