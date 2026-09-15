"""Evaluate action-only private allocation across eight service sites."""

from __future__ import annotations

import json
import math
from pathlib import Path
import random

from dtpr import DecisionTargetedPrivateRelease


SEED = 20260825
SCENARIOS = 50_000
SITES = tuple(f"site_{index}" for index in range(1, 9))
TEAMS = 2
TOTAL_EPSILON = 1.0


def laplace(rng: random.Random, scale: float) -> float:
    u = rng.random() - 0.5
    return -scale * math.copysign(math.log1p(-2.0 * abs(u)), u)


def evaluate() -> dict[str, object]:
    scenario_rng = random.Random(SEED)
    baseline_rng = random.Random(SEED + 1)
    dtpr_seed_rng = random.Random(SEED + 2)
    totals = {
        "full_count_dashboard": {"regret": 0.0, "exact": 0, "captured": 0.0, "oracle": 0.0},
        "dtpr_action_only": {"regret": 0.0, "exact": 0, "captured": 0.0, "oracle": 0.0},
    }

    for _ in range(SCENARIOS):
        # A common city-wide load plus independent site pressure creates both
        # close calls and clear priorities.
        common = scenario_rng.randint(8, 24)
        counts = {
            site: max(0, common + round(scenario_rng.gauss(0.0, 8.0))) for site in SITES
        }
        oracle = sorted(SITES, key=lambda site: counts[site], reverse=True)[:TEAMS]
        oracle_value = sum(counts[site] for site in oracle)

        # Full dashboard: eight counts are released, so sequential composition
        # gives epsilon/8 to each count before an operator selects two sites.
        baseline_scale = 1.0 / (TOTAL_EPSILON / len(SITES))
        noisy_counts = {
            site: count + laplace(baseline_rng, baseline_scale)
            for site, count in counts.items()
        }
        baseline = sorted(SITES, key=lambda site: noisy_counts[site], reverse=True)[:TEAMS]

        # DTPR: no count is released.  Two action selections divide the same
        # total epsilon through sequential composition.
        engine = DecisionTargetedPrivateRelease(
            TOTAL_EPSILON, seed=dtpr_seed_rng.randrange(0, 2**63)
        )
        releases = engine.release_top_k(
            "allocate_emergency_team",
            counts,
            TEAMS,
            TOTAL_EPSILON,
            utility_sensitivity=1.0,
        )
        dtpr = [release.selected_action for release in releases]

        for method, selected in (
            ("full_count_dashboard", baseline),
            ("dtpr_action_only", dtpr),
        ):
            captured = sum(counts[site] for site in selected)
            totals[method]["captured"] += captured
            totals[method]["oracle"] += oracle_value
            totals[method]["regret"] += oracle_value - captured
            totals[method]["exact"] += set(selected) == set(oracle)

    result: dict[str, object] = {
        "scenario": {
            "seed": SEED,
            "scenarios": SCENARIOS,
            "sites": len(SITES),
            "teams": TEAMS,
            "total_epsilon": TOTAL_EPSILON,
        },
        "summary": {},
    }
    for method, values in totals.items():
        result["summary"][method] = {
            "mean_unserved_priority_regret": values["regret"] / SCENARIOS,
            "exact_top_two_rate": values["exact"] / SCENARIOS,
            "captured_priority_fraction": values["captured"] / values["oracle"],
            "released_private_counts": len(SITES) if method == "full_count_dashboard" else 0,
            "released_actions": TEAMS,
        }

    baseline_regret = result["summary"]["full_count_dashboard"][
        "mean_unserved_priority_regret"
    ]
    dtpr_regret = result["summary"]["dtpr_action_only"]["mean_unserved_priority_regret"]
    result["summary"]["regret_reduction"] = 1.0 - dtpr_regret / baseline_regret
    return result


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("multisite_evaluation_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"\nSaved reproducible results to {output}")
