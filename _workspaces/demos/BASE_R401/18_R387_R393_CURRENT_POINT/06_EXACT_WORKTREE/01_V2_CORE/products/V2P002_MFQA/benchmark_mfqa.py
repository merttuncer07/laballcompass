from __future__ import annotations

import json

from mfqa import FidelityChannel, allocate_quasineutral_measurements


FINE = FidelityChannel("fine_transport_assay", noise_variance=0.0025, cost=0.002)
CHEAP = FidelityChannel("cheap_transport_proxy", noise_variance=0.025, cost=0.0002)


def run_case(name: str, *, imbalance: float, correlation: float) -> dict:
    result = allocate_quasineutral_measurements(
        imbalance,
        belief_variance=0.01,
        tolerance=0.05,
        total_budget=0.1,
        fine_channel=FINE,
        cheap_channel=CHEAP,
        pilot_correlation=correlation,
        min_fine=4,
        min_correlation=0.2,
    )
    return {"case": name, "pilot_correlation": correlation, **result.to_dict()}


def main() -> None:
    cases = [
        run_case("near_boundary_high_correlation", imbalance=0.052, correlation=0.92),
        run_case("near_boundary_low_correlation", imbalance=0.052, correlation=0.05),
        run_case("far_from_boundary", imbalance=0.35, correlation=0.92),
    ]
    high, low, far = cases
    summary = {
        "benchmark": "MFQA deterministic regime routing",
        "cases": cases,
        "comparison": {
            "high_correlation_variance_proxy": high["variance_proxy"],
            "low_correlation_variance_proxy": low["variance_proxy"],
            "relative_variance_proxy_reduction_vs_fine_only": (
                1.0 - high["variance_proxy"] / low["variance_proxy"]
            ),
            "far_case_budget_avoided": 0.1 - far["spent_budget"],
        },
        "interpretation": (
            "Decision proximity opens the measurement gate; cross-fidelity correlation decides "
            "whether cheap observations can supplement fine observations. A far-boundary case "
            "buys no measurement rather than spending the available budget automatically."
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
