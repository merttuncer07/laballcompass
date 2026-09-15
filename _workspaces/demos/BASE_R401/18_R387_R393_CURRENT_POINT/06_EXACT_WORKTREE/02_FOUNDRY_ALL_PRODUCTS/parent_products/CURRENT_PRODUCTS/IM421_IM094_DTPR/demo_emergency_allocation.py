"""Construction evaluation for the IM-421 -> IM-094 product prototype.

Scenario: a service dispatches an emergency team when a private count reaches
30.  A conventional dashboard spends the total epsilon equally on 12 released
statistics.  DTPR releases only the operational action and spends the budget on
the decision score.
"""

from __future__ import annotations

import json
from pathlib import Path
import random

from dtpr import DecisionSpec, DecisionTargetedPrivateRelease, allocate_budget


TOTAL_EPSILON = 1.0
THRESHOLD = 30.0
TRIALS_PER_COUNT = 10_000
COUNTS = range(15, 46)
SEED = 20260825


def evaluate() -> dict[str, object]:
    dispatch = DecisionSpec(
        name="dispatch_emergency_team",
        thresholds=(THRESHOLD,),
        actions=("monitor", "dispatch"),
        sensitivity=1.0,
        consequence_weight=5.0,
    )
    dashboard_specs = [dispatch] + [
        DecisionSpec(
            name=f"descriptive_metric_{index:02d}",
            thresholds=(50.0,),
            actions=("low", "high"),
            sensitivity=1.0,
            consequence_weight=0.0,
        )
        for index in range(1, 12)
    ]

    uniform = allocate_budget(dashboard_specs, TOTAL_EPSILON, method="uniform")
    targeted = allocate_budget(dashboard_specs, TOTAL_EPSILON, method="decision_weighted")
    uniform_epsilon = uniform.epsilon_by_decision[dispatch.name]
    targeted_epsilon = targeted.epsilon_by_decision[dispatch.name]

    methods = {
        "full_dashboard_uniform": uniform_epsilon,
        "decision_targeted": targeted_epsilon,
    }
    rng = random.Random(SEED)
    totals = {
        name: {"errors": 0, "false_negatives": 0, "false_positives": 0, "cost": 0.0}
        for name in methods
    }
    per_count: list[dict[str, object]] = []

    for true_count in COUNTS:
        correct_action = dispatch.action_for(true_count)
        count_row: dict[str, object] = {"true_count": true_count, "correct_action": correct_action}
        for method_name, epsilon in methods.items():
            errors = false_negatives = false_positives = 0
            cost = 0.0
            for _ in range(TRIALS_PER_COUNT):
                engine = DecisionTargetedPrivateRelease(
                    total_epsilon=epsilon,
                    seed=rng.randrange(0, 2**63),
                )
                action = engine.release(dispatch, true_count, epsilon).action
                if action != correct_action:
                    errors += 1
                    if correct_action == "dispatch":
                        false_negatives += 1
                        cost += 5.0
                    else:
                        false_positives += 1
                        cost += 1.0
            totals[method_name]["errors"] += errors
            totals[method_name]["false_negatives"] += false_negatives
            totals[method_name]["false_positives"] += false_positives
            totals[method_name]["cost"] += cost
            count_row[f"{method_name}_error_rate"] = errors / TRIALS_PER_COUNT
        per_count.append(count_row)

    observations = len(list(COUNTS)) * TRIALS_PER_COUNT
    summary: dict[str, object] = {}
    for method_name, epsilon in methods.items():
        row = totals[method_name]
        summary[method_name] = {
            "epsilon_for_dispatch": epsilon,
            "laplace_scale": dispatch.sensitivity / epsilon,
            "overall_action_error_rate": row["errors"] / observations,
            "false_negative_rate_all_cases": row["false_negatives"] / observations,
            "false_positive_rate_all_cases": row["false_positives"] / observations,
            "mean_operational_cost": row["cost"] / observations,
        }

    baseline_cost = summary["full_dashboard_uniform"]["mean_operational_cost"]
    targeted_cost = summary["decision_targeted"]["mean_operational_cost"]
    summary["operational_cost_reduction"] = 1.0 - targeted_cost / baseline_cost
    summary["action_error_reduction"] = 1.0 - (
        summary["decision_targeted"]["overall_action_error_rate"]
        / summary["full_dashboard_uniform"]["overall_action_error_rate"]
    )

    return {
        "scenario": {
            "total_epsilon": TOTAL_EPSILON,
            "threshold": THRESHOLD,
            "trials_per_count": TRIALS_PER_COUNT,
            "true_count_range": [min(COUNTS), max(COUNTS)],
            "dashboard_query_count": len(dashboard_specs),
            "seed": SEED,
        },
        "summary": summary,
        "per_count": per_count,
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("evaluation_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"\nSaved reproducible results to {output}")

