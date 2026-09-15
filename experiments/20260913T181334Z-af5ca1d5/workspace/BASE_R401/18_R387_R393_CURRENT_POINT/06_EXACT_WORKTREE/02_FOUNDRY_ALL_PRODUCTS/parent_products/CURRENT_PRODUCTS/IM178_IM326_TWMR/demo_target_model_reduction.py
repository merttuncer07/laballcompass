from __future__ import annotations

import json
from pathlib import Path

from twmr import TargetWeightedModelReducer


def evaluate() -> dict[str, object]:
    reducer = TargetWeightedModelReducer(
        system_matrix=[
            [0.95, 0, 0, 0, 0],
            [0, 0.85, 0, 0, 0],
            [0, 0, 0.70, 0, 0],
            [0, 0, 0, 0.60, 0],
            [0, 0, 0, 0, 0.50],
        ],
        input_matrix=[[8.0], [2.0], [1.5], [1.0], [0.8]],
        target_output_matrix=[[0.01, 3.0, 2.0, 0.2, 0.1]],
        state_names=["large_hidden_energy", "target_driver_a", "target_driver_b", "minor_c", "minor_d"],
    )
    target = reducer.reduce(retain_count=2, horizon=25)
    energy = reducer.energy_baseline(retain_count=2, horizon=25)
    return {
        "retain_count": 2,
        "target_weighted": target.as_dict(),
        "state_energy_baseline": energy.as_dict(),
        "relative_error_reduction": 1.0
        - target.relative_target_error / energy.relative_target_error,
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("target_model_reduction_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
