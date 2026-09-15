from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from jarb_native import LAB, actual_joint_loss, candidate, removal_control


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "R400_JARB_NATIVE_SENSITIVITY_RECEIPT.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "minimum": float(np.min(array)),
        "p10": float(np.quantile(array, 0.10)),
        "median": float(np.median(array)),
        "p90": float(np.quantile(array, 0.90)),
        "maximum": float(np.max(array)),
    }


def main() -> None:
    rng = np.random.default_rng(401)
    observations = []
    for shell_id in range(2000):
        sensors = rng.uniform(0.0, 1.0, size=(5, 3))
        declared = rng.lognormal(mean=0.0, sigma=1.0, size=3)
        budget = int(rng.integers(5, 14))
        proposed = candidate(declared, sensors, budget)
        control = removal_control(declared, sensors, budget)
        declared_gain = actual_joint_loss(control, sensors, declared) - actual_joint_loss(
            proposed, sensors, declared
        )
        permuted_truth = declared[rng.permutation(3)]
        hidden_gain = actual_joint_loss(control, sensors, permuted_truth) - actual_joint_loss(
            proposed, sensors, permuted_truth
        )
        observations.append(
            {
                "shell_id": shell_id,
                "budget": budget,
                "split_changed": proposed.sensor_budget != control.sensor_budget,
                "native_decision_changed": (proposed.sensors, proposed.modes)
                != (control.sensors, control.modes),
                "declared_gain": float(declared_gain),
                "permuted_truth_gain": float(hidden_gain),
            }
        )

    changed = [row for row in observations if row["native_decision_changed"]]
    parent_root = LAB / "R392_EXACT_BASE" / "01_V2_CORE" / "products"
    receipt = {
        "model_version": "R400_JARB_NATIVE_SENSITIVITY_V1",
        "status": "PASS_MECHANICS_EXPERIMENT_ONLY",
        "seed": 401,
        "shell_count": len(observations),
        "split_changed_count": sum(row["split_changed"] for row in observations),
        "native_decision_changed_count": len(changed),
        "native_decision_changed_fraction": len(changed) / len(observations),
        "declared_gain_positive_count": sum(row["declared_gain"] > 1e-12 for row in observations),
        "declared_gain_stats_changed_shells": stats([row["declared_gain"] for row in changed]),
        "permuted_truth_harm_count": sum(row["permuted_truth_gain"] < -1e-12 for row in observations),
        "permuted_truth_harm_fraction": sum(row["permuted_truth_gain"] < -1e-12 for row in observations) / len(observations),
        "permuted_truth_gain_stats": stats([row["permuted_truth_gain"] for row in observations]),
        "code_sha256": digest(HERE / "jarb_native.py"),
        "test_sha256": digest(HERE / "test_jarb_native.py"),
        "native_parent_sha256": {
            "V2P054_CADSBC/cadsbc.py": digest(parent_root / "V2P054_CADSBC" / "cadsbc.py"),
            "V2P057_REOC/reoc.py": digest(parent_root / "V2P057_REOC" / "reoc.py"),
        },
        "evidence_boundary": "Synthetic deterministic sensitivity; not empirical validation or novel theory.",
        "promotion_status": "PENDING_QUALITY_ADJUDICATION",
    }
    OUTPUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
