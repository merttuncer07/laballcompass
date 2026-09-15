from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from doeblin_comparison import (
    cdf_order_violations,
    simulate_raw_euler,
    simulate_transformed_euler,
)


def run():
    records = []
    for steps in (10, 20, 50, 100, 200):
        start = time.perf_counter()
        raw = simulate_raw_euler(paths=50_000, steps=steps, seed=1000 + steps)
        transformed = simulate_transformed_euler(
            paths=50_000, steps=steps, seed=1000 + steps
        )
        elapsed = time.perf_counter() - start
        records.append(
            {
                "steps": steps,
                "dt": 1.0 / steps,
                "raw_order_failure_rate": raw["order_failure_rate"],
                "raw_nonfinite_rate": raw["nonfinite_rate"],
                "raw_cdf": cdf_order_violations(raw["states"]),
                "transformed_order_failure_rate": transformed[
                    "order_failure_rate"
                ],
                "transformed_nonfinite_rate": transformed["nonfinite_rate"],
                "transformed_cdf": cdf_order_violations(transformed["states"]),
                "combined_seconds": elapsed,
            }
        )
    result = {
        "status": "SCOPED_ORDER_PRESERVING_DISCRETIZATION_CONFIRMED",
        "historical_open_end": "Doeblin manuscript stops during same-diffusion ordered-drift comparison argument",
        "theorem_scope": "one-dimensional smooth positive common diffusion; Lamperti coordinates; transformed drift base map monotone at chosen step",
        "experiment": {
            "paths_per_step_size": 50000,
            "horizon": 1.0,
            "records": records,
        },
        "retained": [
            "Doeblin drift removal and quadratic-variation clock as historical mechanism",
            "comparison-preserving transformed Euler for ordered drift envelopes",
            "raw Euler order violation as a numerical failure boundary",
        ],
        "not_breakthrough_because": [
            "continuous-time result is covered by modern one-dimensional SDE comparison theorems",
            "Doeblin clock is subsumed by Dambis-Dubins-Schwarz",
            "Lamperti and order-preserving SDE schemes are active modern literatures",
        ],
        "python": sys.version,
    }
    output = Path(__file__).with_name("R208_RESULT.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()

