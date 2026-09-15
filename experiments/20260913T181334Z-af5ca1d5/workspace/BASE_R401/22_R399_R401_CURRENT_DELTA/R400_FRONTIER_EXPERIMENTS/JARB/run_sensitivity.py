from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from jarb_experiment import actual_joint_loss, candidate, removal_control


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "R400_JARB_SENSITIVITY_RECEIPT.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantiles(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "minimum": float(np.min(array)),
        "p10": float(np.quantile(array, 0.10)),
        "median": float(np.median(array)),
        "p90": float(np.quantile(array, 0.90)),
        "maximum": float(np.max(array)),
    }


def main() -> None:
    rng = np.random.default_rng(400)
    rows = []
    for shell_id in range(1000):
        sensors = rng.uniform(0.0, 1.0, size=(4, 3))
        declared = rng.lognormal(mean=0.0, sigma=0.9, size=3)
        budget = int(rng.integers(5, 11))
        proposed = candidate(declared, sensors, budget)
        control = removal_control(declared, sensors, budget)
        declared_gain = actual_joint_loss(control, sensors, declared) - actual_joint_loss(
            proposed, sensors, declared
        )
        truth = declared[rng.permutation(3)]
        hidden_truth_gain = actual_joint_loss(control, sensors, truth) - actual_joint_loss(
            proposed, sensors, truth
        )
        rows.append(
            {
                "shell_id": shell_id,
                "budget": budget,
                "decision_changed": (proposed.sensors, proposed.modes) != (control.sensors, control.modes),
                "declared_gain": float(declared_gain),
                "hidden_truth_gain_after_permutation": float(hidden_truth_gain),
            }
        )

    changed = [row for row in rows if row["decision_changed"]]
    receipt = {
        "model_version": "R400_JARB_SENSITIVITY_V1",
        "status": "PASS_MECHANICS_EXPERIMENT_ONLY",
        "seed": 400,
        "shell_count": len(rows),
        "decision_changed_count": len(changed),
        "decision_changed_fraction": len(changed) / len(rows),
        "declared_gain_positive_count": sum(row["declared_gain"] > 1e-12 for row in rows),
        "declared_gain_quantiles_all_shells": quantiles([row["declared_gain"] for row in rows]),
        "declared_gain_quantiles_changed_shells": quantiles([row["declared_gain"] for row in changed]),
        "miscalibrated_truth_harm_count": sum(row["hidden_truth_gain_after_permutation"] < -1e-12 for row in rows),
        "miscalibrated_truth_harm_fraction": sum(row["hidden_truth_gain_after_permutation"] < -1e-12 for row in rows) / len(rows),
        "miscalibrated_truth_gain_quantiles": quantiles(
            [row["hidden_truth_gain_after_permutation"] for row in rows]
        ),
        "code_sha256": digest(HERE / "jarb_experiment.py"),
        "test_sha256": digest(HERE / "test_jarb_experiment.py"),
        "evidence_boundary": "Synthetic deterministic sensitivity only; declared-objective improvement is not empirical validation.",
        "promotion_status": "EXPERIMENT_ONLY_NOT_V2P059",
    }
    OUTPUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
