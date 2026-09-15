from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from dre import DecisionRelevantExplorer, GaussianArm, greedy_choice, uncertainty_only_choice


def run_episode(rng: np.random.Generator, policy: str, horizon: int = 80) -> tuple[float, bool, int]:
    true_means = {"A": 1.00, "B": 1.05, "C": -3.00}
    arms = {
        "A": GaussianArm("A", 0.90, 0.04, 1.0),
        "B": GaussianArm("B", 0.85, 0.09, 1.0),
        "C": GaussianArm("C", -3.00, 4.00, 1.0),
    }
    explorer = DecisionRelevantExplorer()
    pseudo_regret = 0.0
    irrelevant_pulls = 0
    for step in range(horizon):
        current = list(arms.values())
        if policy == "decision_relevant":
            chosen = explorer.choose(current, horizon - step)
        elif policy == "uncertainty_only":
            chosen = uncertainty_only_choice(current)
        elif policy == "greedy":
            chosen = greedy_choice(current)
        else:
            raise ValueError(policy)
        pseudo_regret += max(true_means.values()) - true_means[chosen]
        irrelevant_pulls += chosen == "C"
        observation = rng.normal(true_means[chosen], 1.0)
        arms[chosen] = arms[chosen].update(float(observation))
    recommendation = max(arms.values(), key=lambda arm: arm.mean).name
    return pseudo_regret, recommendation == "B", irrelevant_pulls


def evaluate() -> dict[str, object]:
    rng = np.random.default_rng(20260825)
    episodes = 2000
    result = {}
    for policy in ("uncertainty_only", "greedy", "decision_relevant"):
        rows = [run_episode(rng, policy) for _ in range(episodes)]
        result[policy] = {
            "mean_pseudo_regret": float(np.mean([row[0] for row in rows])),
            "final_best_action_accuracy": float(np.mean([row[1] for row in rows])),
            "mean_irrelevant_high_variance_pulls": float(np.mean([row[2] for row in rows])),
        }
    baseline = result["uncertainty_only"]["mean_pseudo_regret"]
    result["regret_reduction_vs_uncertainty_only"] = 1.0 - (
        result["decision_relevant"]["mean_pseudo_regret"] / baseline
    )
    return {"episodes": episodes, "horizon": 80, "results": result}


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("decision_exploration_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
