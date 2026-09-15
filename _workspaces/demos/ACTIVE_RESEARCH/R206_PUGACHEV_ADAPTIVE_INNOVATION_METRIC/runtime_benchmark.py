from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import third_pass
from adaptive_metric import AdaptationConfig, adaptive_compiled_sequence
from automatic_psd_closure import compile_closure, compiled_sequence


HERE = Path(__file__).resolve().parent


def median_time(function, repeats=5):
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        function()
        samples.append(time.perf_counter() - started)
    return float(np.median(samples))


def run():
    records = []
    for dimension in (2, 4, 8, 16):
        closure = compile_closure(dimension, "gaussian")[0]
        transition, process_scale, cubic, correlation = (
            third_pass.scenario_parameters(dimension, "dense_equicorrelation")
        )
        rng = np.random.default_rng(2_660_000 + dimension)
        _, measured = third_pass.correlated_system_paths(
            rng,
            "gaussian",
            trajectories=20,
            steps=70,
            transition=transition,
            process_scale=process_scale,
            cubic=cubic,
            correlation=correlation,
        )
        legacy = lambda: compiled_sequence(
            closure, measured, transition, process_scale, cubic
        )
        compound = lambda: adaptive_compiled_sequence(
            closure,
            measured,
            transition,
            process_scale,
            cubic,
            AdaptationConfig(
                "compound",
                gain=0.08,
                shrinkage=0.82,
                activation_threshold=0.06,
            ),
        )
        full_shared = lambda: adaptive_compiled_sequence(
            closure,
            measured,
            transition,
            process_scale,
            cubic,
            AdaptationConfig(
                "full",
                gain=0.11,
                shrinkage=0.86,
                shared_across_batch=True,
                activation_threshold=0.08,
            ),
        )
        # Warm caches and linear algebra dispatch before timing.
        legacy()
        compound()
        full_shared()
        legacy_seconds = median_time(legacy)
        compound_seconds = median_time(compound)
        full_seconds = median_time(full_shared)
        records.append(
            {
                "dimension": dimension,
                "updates": 20 * 70,
                "legacy_seconds": legacy_seconds,
                "compound_seconds": compound_seconds,
                "full_shared_seconds": full_seconds,
                "compound_overhead_ratio": compound_seconds / legacy_seconds,
                "full_shared_overhead_ratio": full_seconds / legacy_seconds,
            }
        )
    return {"records": records}


if __name__ == "__main__":
    result = run()
    path = HERE / "R206_RUNTIME.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
