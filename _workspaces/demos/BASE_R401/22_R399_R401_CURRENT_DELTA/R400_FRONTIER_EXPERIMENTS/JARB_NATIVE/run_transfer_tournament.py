from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from jarb_native import candidate, removal_control


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "R400_JARB_NATIVE_TRANSFER_TOURNAMENT.json"
DECLARED = np.asarray([0.24978747391615905, 0.22466954832223132, 2.147769467852834])
SENSORS = np.asarray(
    [
        [0.04, 0.73, 0.59],
        [0.86, 0.19, 0.76],
        [0.75, 0.21, 0.43],
        [0.46, 0.52, 0.35],
        [0.22, 0.59, 0.20],
    ]
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def downstream_loss(decision, states, full_noise, *, noise_scale: float, coarse_step: float) -> float:
    selected = list(decision.sensors)
    geometry = SENSORS[selected]
    measurements = states @ geometry.T + noise_scale * full_noise[:, selected]
    ridge_inverse = np.linalg.solve(geometry.T @ geometry + 0.05 * np.eye(3), geometry.T)
    estimate = measurements @ ridge_inverse.T
    steps = np.asarray(
        [{"coarse": coarse_step, "balanced": 0.35, "fine": 0.10}[mode] for mode in decision.modes]
    )
    represented = np.round(estimate / steps) * steps
    return float(np.mean(np.sum((states - represented) ** 2 * DECLARED, axis=1)))


def main() -> None:
    proposed = candidate(DECLARED, SENSORS, 9)
    control = removal_control(DECLARED, SENSORS, 9)
    rng = np.random.default_rng(403)
    trials = 100_000
    states = rng.normal(size=(trials, 3))
    full_noise = rng.normal(size=(trials, 5))
    cells = []
    for noise_scale in (0.02, 0.10, 0.40):
        for coarse_step in (0.40, 0.60, 0.80, 1.00, 1.50, 2.00, 3.00):
            candidate_loss = downstream_loss(
                proposed, states, full_noise, noise_scale=noise_scale, coarse_step=coarse_step
            )
            control_loss = downstream_loss(
                control, states, full_noise, noise_scale=noise_scale, coarse_step=coarse_step
            )
            cells.append(
                {
                    "noise_scale": noise_scale,
                    "coarse_quantization_step": coarse_step,
                    "candidate_loss": candidate_loss,
                    "control_loss": control_loss,
                    "candidate_gain": control_loss - candidate_loss,
                    "winner": "CANDIDATE" if candidate_loss < control_loss else "REMOVAL_CONTROL",
                }
            )
    candidate_wins = [cell for cell in cells if cell["winner"] == "CANDIDATE"]
    receipt = {
        "model_version": "R400_JARB_NATIVE_TRANSFER_TOURNAMENT_V1",
        "status": "COMPLETE_NEGATIVE_OR_NARROW_TRANSFER_RESULT",
        "seed": 403,
        "common_random_trials_per_cell": trials,
        "cell_count": len(cells),
        "candidate_win_count": len(candidate_wins),
        "removal_control_win_count": len(cells) - len(candidate_wins),
        "candidate_win_fraction": len(candidate_wins) / len(cells),
        "candidate_win_region": {
            "minimum_coarse_quantization_step": min(
                (cell["coarse_quantization_step"] for cell in candidate_wins), default=None
            ),
            "noise_scales": sorted({cell["noise_scale"] for cell in candidate_wins}),
        },
        "candidate_decision": proposed.to_dict(),
        "removal_control_decision": control.to_dict(),
        "cells": cells,
        "code_sha256": sha256(HERE / "jarb_native.py"),
        "evidence_boundary": "Synthetic transfer tournament with common random draws; not real-world empirical validation.",
        "promotion_status": "DO_NOT_PROMOTE_UNLESS_TRANSFER_REGION_IS_MATERIAL_AND_JUSTIFIED",
    }
    OUTPUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "cells": len(cells),
                "candidate_wins": len(candidate_wins),
                "removal_control_wins": len(cells) - len(candidate_wins),
                "candidate_win_region": receipt["candidate_win_region"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
