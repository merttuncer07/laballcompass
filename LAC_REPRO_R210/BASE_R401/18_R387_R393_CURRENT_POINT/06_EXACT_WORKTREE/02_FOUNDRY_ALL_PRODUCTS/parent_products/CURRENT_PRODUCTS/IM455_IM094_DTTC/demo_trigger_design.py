from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from dttc import DecisionTargetedTriggerDesigner, TriggerCandidate


SEED = 20260825
N = 300_000


def evaluate() -> dict[str, object]:
    rng = np.random.default_rng(SEED)
    loss = rng.normal(0.2, 1.2, N)
    event = loss > 1.5
    local = loss + rng.normal(0.0, 0.2, N)
    regional = loss + rng.normal(0.0, 0.7, N)
    manipulable = (~event) & (rng.random(N) < 0.40)
    local[manipulable] += 3.0

    designer = DecisionTargetedTriggerDesigner(
        false_negative_cost=5.0,
        false_positive_cost=1.0,
        manipulation_cost_weight=1.0,
        threshold_grid_size=401,
    )
    result = designer.design(
        [
            TriggerCandidate("local", verification_cost=0.01, manipulation_exposure=0.20),
            TriggerCandidate("regional", verification_cost=0.04, manipulation_exposure=0.0),
        ],
        {"local": local, "regional": regional},
        event,
        loss,
    )
    result["scenario"] = {
        "seed": SEED,
        "cases": N,
        "event_rate": float(np.mean(event)),
        "realized_local_manipulation_rate": float(np.mean(manipulable)),
        "loss_distribution": "Normal(0.2, 1.2^2)",
    }
    return result


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("trigger_design_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
