from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from planner import (
    InspectionMode,
    InspectionPlanner,
    InspectionTarget,
    main,
    plan_from_config,
)


class InspectionPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.modes = (
            InspectionMode("cheap", 1, 4, 4),
            InspectionMode("fine", 5, 1, 1),
        )

    def test_higher_consequence_target_receives_limited_upgrade(self) -> None:
        planner = InspectionPlanner(
            (
                InspectionTarget("critical", 1, 1, 10),
                InspectionTarget("minor", 1, 1, 1),
            ),
            self.modes,
        )
        result = planner.plan(6)
        chosen = {row["target"]: row["mode"] for row in result["plan"]["selections"]}
        self.assertEqual(chosen, {"critical": "fine", "minor": "cheap"})

    def test_budget_is_respected(self) -> None:
        planner = InspectionPlanner(
            (InspectionTarget("a", 1, 1, 1), InspectionTarget("b", 1, 1, 1)),
            self.modes,
        )
        self.assertLessEqual(planner.plan(6)["plan"]["total_cost"], 6)

    def test_infeasible_budget_reports_minimum(self) -> None:
        planner = InspectionPlanner((InspectionTarget("a", 1, 1, 1),), self.modes)
        with self.assertRaisesRegex(ValueError, "minimum required budget is 1"):
            planner.plan(0.5)

    def test_target_mode_restriction_is_enforced(self) -> None:
        planner = InspectionPlanner(
            (InspectionTarget("restricted", 1, 1, 1, allowed_modes=("cheap",)),),
            self.modes,
        )
        self.assertEqual(planner.plan(10)["plan"]["selections"][0]["mode"], "cheap")

    def test_uniform_comparator_is_reported(self) -> None:
        planner = InspectionPlanner(
            (InspectionTarget("a", 4, 1, 4), InspectionTarget("b", 1, 4, 1)),
            self.modes,
        )
        result = planner.plan(6)
        self.assertIsNotNone(result["comparison"]["best_affordable_uniform_plan"])
        self.assertGreaterEqual(result["comparison"]["loss_reduction_vs_uniform_percent"], 0)

    def test_exact_frontier_matches_bruteforce_small_case(self) -> None:
        modes = (
            InspectionMode("x", 1.1, 5, 2),
            InspectionMode("y", 2.3, 2, 3),
            InspectionMode("z", 4.7, 1, 1),
        )
        targets = (
            InspectionTarget("a", 2, 1, 4),
            InspectionTarget("b", 1, 3, 2),
            InspectionTarget("c", 4, 1, 1),
        )
        planner = InspectionPlanner(targets, modes)
        result = planner.plan(7.0)["plan"]
        brute = []
        for first in modes:
            for second in modes:
                for third in modes:
                    choices = tuple(zip(targets, (first, second, third)))
                    cost = sum(planner.choice_cost(t, m) for t, m in choices)
                    loss = sum(planner.decision_loss(t, m) for t, m in choices)
                    if cost <= 7.0:
                        brute.append((loss, cost))
        expected_loss, expected_cost = min(brute)
        self.assertAlmostEqual(result["total_cost"], expected_cost)
        self.assertAlmostEqual(result["total_decision_loss"], expected_loss)

    def test_stress_case_can_change_allocation(self) -> None:
        config = {
            "budget": 6,
            "targets": [
                {"name": "a", "urgency_weight": 1, "diagnostic_weight": 1, "consequence": 5},
                {"name": "b", "urgency_weight": 1, "diagnostic_weight": 1, "consequence": 1},
            ],
            "modes": [
                {"name": "cheap", "cost": 1, "delay_error": 4, "diagnostic_error": 4},
                {"name": "fine", "cost": 5, "delay_error": 1, "diagnostic_error": 1},
            ],
            "stress_cases": [
                {"name": "b critical", "consequence_multipliers": {"b": 10}}
            ],
        }
        result = plan_from_config(config)
        self.assertFalse(result["stress_cases"][0]["stable"])

    def test_cli_writes_json_and_markdown(self) -> None:
        source = Path(__file__).with_name("example_maintenance.json")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "plan.json"
            report = Path(temp) / "plan.md"
            self.assertEqual(main([str(source), "--output", str(output), "--report", str(report)]), 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["product"], "CONSEQUENCE_AWARE_INSPECTION_PLANNER_V1")
            self.assertIn("Selected inspection modes", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
