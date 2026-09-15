from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ows import OverlapAwareWeightStabilizer


def evaluate() -> dict[str, object]:
    rng = np.random.default_rng(20260825)
    repetitions = 400
    sample_size = 500
    target_shift = 2.0
    # High-precision target truth for the bounded outcome.
    target_x = rng.normal(target_shift, 1.0, 2_000_000)
    truth = float(0.3 * np.mean(np.tanh(target_x)))
    raw_errors = []
    stabilized_errors = []
    audits = []
    selected_caps = []
    for _ in range(repetitions):
        x = rng.normal(0.0, 1.0, sample_size)
        y = 0.3 * np.tanh(x) + rng.uniform(-0.7, 0.7, sample_size)
        weights = np.exp(target_shift * x - 0.5 * target_shift**2)
        engine = OverlapAwareWeightStabilizer(
            fragile_ess_fraction=0.10, bias_aversion=0.001
        )
        audits.append(engine.audit(weights))
        result = engine.fit(weights, y, (-1.0, 1.0))
        raw_errors.append((result.raw_estimate - truth) ** 2)
        stabilized_errors.append((result.stabilized_estimate - truth) ** 2)
        selected_caps.append(result.selected_cap)
    raw_mse = float(np.mean(raw_errors))
    stabilized_mse = float(np.mean(stabilized_errors))
    return {
        "target_truth": truth,
        "repetitions": repetitions,
        "sample_size": sample_size,
        "target_shift": target_shift,
        "raw_exact_weight_mse": raw_mse,
        "stabilized_weight_mse": stabilized_mse,
        "mse_reduction": 1.0 - stabilized_mse / raw_mse,
        "median_selected_cap": float(np.median(selected_caps)),
        "median_effective_sample_fraction": float(
            np.median([audit.effective_sample_fraction for audit in audits])
        ),
        "fragile_support_rate": float(
            np.mean([audit.status == "SUPPORT_FRAGILE" for audit in audits])
        ),
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("weight_stabilization_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
