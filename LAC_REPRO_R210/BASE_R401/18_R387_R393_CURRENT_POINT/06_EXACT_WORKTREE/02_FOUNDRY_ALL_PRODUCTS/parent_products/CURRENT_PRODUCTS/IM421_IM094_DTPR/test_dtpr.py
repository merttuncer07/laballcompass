from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from dtpr import (
    DecisionSpec,
    DecisionTargetedPrivateRelease,
    allocate_budget,
    count_score,
)
from dtpr_cli import HashChainLedger, run_policy


class DecisionTargetedPrivateReleaseTests(unittest.TestCase):
    def test_threshold_actions(self) -> None:
        spec = DecisionSpec("triage", (10.0, 20.0), ("green", "amber", "red"), 1.0)
        self.assertEqual(spec.action_for(9.9), "green")
        self.assertEqual(spec.action_for(10.0), "amber")
        self.assertEqual(spec.action_for(20.0), "red")

    def test_weighted_budget_uses_cube_root_solution(self) -> None:
        specs = [
            DecisionSpec("a", (0.0,), ("no", "yes"), 1.0, 1.0),
            DecisionSpec("b", (0.0,), ("no", "yes"), 2.0, 2.0),
        ]
        plan = allocate_budget(specs, 1.0)
        expected_ratio = (2.0 * 2.0**2) ** (1.0 / 3.0)
        actual_ratio = plan.epsilon_by_decision["b"] / plan.epsilon_by_decision["a"]
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=12)
        self.assertAlmostEqual(plan.epsilon_spent, 1.0, places=12)

    def test_zero_consequence_query_is_not_released(self) -> None:
        specs = [
            DecisionSpec("action", (5.0,), ("wait", "go"), 1.0, 1.0),
            DecisionSpec("decoration", (5.0,), ("low", "high"), 1.0, 0.0),
        ]
        plan = allocate_budget(specs, 0.8)
        self.assertEqual(plan.epsilon_by_decision["decoration"], 0.0)
        engine = DecisionTargetedPrivateRelease(0.8, seed=1)
        releases = engine.release_plan(specs, {"action": 7.0}, plan)
        self.assertEqual([release.decision for release in releases], ["action"])
        self.assertAlmostEqual(engine.remaining_epsilon, 0.0, places=12)

    def test_raw_score_hidden_by_default(self) -> None:
        spec = DecisionSpec("action", (5.0,), ("wait", "go"), 1.0)
        engine = DecisionTargetedPrivateRelease(1.0, seed=7)
        release = engine.release(spec, 8.0, 1.0)
        self.assertIsNone(release.noisy_score)
        self.assertIn(release.action, {"wait", "go"})

    def test_budget_accountant_blocks_overspend(self) -> None:
        spec = DecisionSpec("action", (5.0,), ("wait", "go"), 1.0)
        engine = DecisionTargetedPrivateRelease(1.0, seed=7)
        engine.release(spec, 8.0, 0.6)
        with self.assertRaises(RuntimeError):
            engine.release(spec, 8.0, 0.5)

    def test_count_score_has_expected_value(self) -> None:
        self.assertEqual(count_score([True, False, True, True]), 3)

    def test_argmax_release_returns_only_a_candidate_action(self) -> None:
        engine = DecisionTargetedPrivateRelease(1.0, seed=3)
        release = engine.release_argmax(
            "choose_site", {"north": 2.0, "south": 9.0}, 1.0, 1.0
        )
        self.assertIn(release.selected_action, {"north", "south"})
        self.assertAlmostEqual(engine.remaining_epsilon, 0.0, places=12)

    def test_top_k_is_unique_and_composes_to_total_budget(self) -> None:
        engine = DecisionTargetedPrivateRelease(0.9, seed=4)
        releases = engine.release_top_k(
            "allocate", {"a": 2.0, "b": 5.0, "c": 8.0}, 2, 0.9, 1.0
        )
        selected = [release.selected_action for release in releases]
        self.assertEqual(len(set(selected)), 2)
        self.assertAlmostEqual(sum(release.epsilon for release in releases), 0.9, places=12)
        self.assertAlmostEqual(engine.remaining_epsilon, 0.0, places=12)

    def test_csv_policy_outputs_action_and_enforces_lifetime_budget(self) -> None:
        base = Path(__file__).parent
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "privacy_ledger.jsonl"
            result = run_policy(
                base / "example_policy.json",
                base / "example_records.csv",
                ledger_path,
                seed=11,
            )
            self.assertEqual(len(result["releases"]), 1)
            self.assertNotIn("noisy_score", result["releases"][0])
            ledger = HashChainLedger(ledger_path)
            self.assertAlmostEqual(ledger.epsilon_spent, 0.25, places=12)
            for seed in (12, 13, 14):
                run_policy(
                    base / "example_policy.json",
                    base / "example_records.csv",
                    ledger_path,
                    seed=seed,
                )
            with self.assertRaises(RuntimeError):
                run_policy(
                    base / "example_policy.json",
                    base / "example_records.csv",
                    ledger_path,
                    seed=15,
                )


if __name__ == "__main__":
    unittest.main()
