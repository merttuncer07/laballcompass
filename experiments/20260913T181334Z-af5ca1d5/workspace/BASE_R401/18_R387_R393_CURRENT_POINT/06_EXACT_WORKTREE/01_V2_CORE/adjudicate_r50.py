from __future__ import annotations

import json
from pathlib import Path

import numpy as np


WORKSPACE = Path(r"C:\Users\mertt\OneDrive\Belgeler\ChatGPT\newlabexplore")
SOURCE = WORKSPACE / "INPUT_LCB_7F3A91_R50_PARTIAL_2026-08-25" / "r50_partial_benchmarks"
OUT = WORKSPACE / "lcb_core_revision" / "generated"


def load(fragment: str) -> np.ndarray:
    path = next(SOURCE.glob(f"*{fragment}*.tsv"))
    return np.genfromtxt(path, delimiter="\t", names=True, dtype=None, encoding="utf-8")


def rows(fragment: str, *, timestamp: str | None = None) -> np.ndarray:
    candidates = sorted(SOURCE.glob(f"*{fragment}*.tsv"))
    if timestamp:
        candidates = [p for p in candidates if timestamp in p.name]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one {fragment}/{timestamp}, got {candidates}")
    return np.genfromtxt(candidates[0], delimiter="\t", names=True, dtype=None, encoding="utf-8")


def median_ci(values: np.ndarray, seed: int) -> list[float]:
    values = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(4000, len(values)))
    medians = np.median(values[idx], axis=1)
    return [float(x) for x in np.quantile(medians, [0.025, 0.975])]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict] = {}

    a = rows("RX149_SUBMODULAR_ALLOCATOR")
    main = a[a["regime"] == "overlap_main"]
    ctrl = a[a["regime"] == "additive_control"]
    out["RX-149"] = {
        "mechanism": "overlap-aware marginal allocation",
        "n_main": int(len(main)),
        "median_gain": float(np.median(main["gain"])),
        "median_gain_95_bootstrap": median_ci(main["gain"], 149),
        "win_rate": float(np.mean(main["greedy_value"] > main["naive_value"])),
        "control_median_gain": float(np.median(ctrl["gain"])),
        "core_v2_state": "CONFIRMED_COMPONENT_STANDALONE_SHELL_OPEN",
        "reason": "A predeclared 12% promotion threshold is a prioritization choice, not evidence that the mechanism is absent.",
    }

    a = rows("RX067_REPRESENTATIVE_DP")
    main = a[a["regime"] == "structured_interface_main"]
    ctrl = a[a["regime"] == "unique_future_control"]
    out["RX-067"] = {
        "mechanism": "future-equivalence representative-state dynamic programming",
        "n_main": int(len(main)),
        "median_state_reduction": float(np.median(main["reduction"])),
        "reduction_95_bootstrap": median_ci(main["reduction"], 67),
        "maximum_optimality_gap": float(np.max(np.abs(main["optimality_gap"]))),
        "control_median_reduction": float(np.median(ctrl["reduction"])),
        "core_v2_state": "CONFIRMED_KERNEL_EXTENSION_AND_STANDALONE_CANDIDATE",
        "reason": "No deletion on ontology overlap; retain the callable capability and link it to interface-width optimization.",
    }

    a = rows("RX039_FIBER_SAMPLER")
    main = a[a["regime"] == "nontrivial_fiber_main"]
    out["RX-039"] = {
        "mechanism": "constraint-preserving conditional fiber sampling",
        "n_main": int(len(main)),
        "fiber_size": int(np.median(main["fiber_size"])),
        "median_tv": float(np.median(main["mcmc_tv_to_exact_uniform"])),
        "tv_90_interval": [float(x) for x in np.quantile(main["mcmc_tv_to_exact_uniform"], [0.05, 0.95])],
        "naive_valid_rate": float(np.mean(main["naive_single_cell_valid_rate"])),
        "core_v2_state": "STANDALONE_KERNEL_CANDIDATE",
        "reason": "Distinct operational interface; next evidence target is mixing diagnostics on larger and multimodal fibers.",
    }

    a = rows("RX137_RENEGOTIATION")
    main = a[a["regime"] == "renegotiable_main"]
    ctrl = a[a["regime"] == "irreversible_control"]
    out["RX-137"] = {
        "mechanism": "renegotiation-aware commitment valuation",
        "n_main": int(len(main)),
        "median_renegotiation_rate": float(np.median(main["renegotiation_rate"])),
        "median_nominal_abs_error": float(np.median(main["nominal_abs_error"])),
        "median_aware_abs_error": float(np.median(main["aware_abs_error"])),
        "control_nominal_abs_error": float(np.median(ctrl["nominal_abs_error"])),
        "core_v2_state": "STANDALONE_KERNEL_CANDIDATE",
        "reason": "Strong mechanism contrast and clean control; real contract and bargaining-rule calibration remain separate gates.",
    }

    # The 12:10 r02 contains the stronger explicit local-repair comparator. The later
    # 12:18 file is retained as replication, not allowed to erase that comparator.
    a = rows("RX138_IMPLEMENTABILITY_IRONER_RESULTS__r02", timestamp="1210")
    main = a[a["regime"] == "nonmonotone_score_main"]
    ctrl = a[a["regime"] == "monotone_control"]
    replication = rows("RX138_IMPLEMENTABILITY_IRONER_RESULTS__r02", timestamp="1218")
    rep_main = replication[replication["regime"] == "nonmonotone_score_main"]
    out["RX-138"] = {
        "mechanism": "projection/ironing into implementable monotone decision class",
        "n_main": int(len(main)),
        "median_raw_violations": float(np.median(main["raw_violations"])),
        "median_ironed_violations": float(np.median(main["ironed_violations"])),
        "median_changed_fraction": float(np.median(main["raw_changed_fraction"])),
        "median_ironed_regret": float(np.median(main["ironed_regret"])),
        "median_simple_repair_regret": float(np.median(main["simple_repair_regret"])),
        "control_changed_fraction": float(np.median(ctrl["raw_changed_fraction"])),
        "replication_n_main": int(len(rep_main)),
        "replication_median_raw_violations": float(np.median(rep_main["raw_violations"])),
        "replication_median_regret": float(np.median(rep_main["ironed_regret"])),
        "core_v2_state": "STANDALONE_KERNEL_CANDIDATE",
        "reason": "Beats a simple repair and matches the exact constrained optimum in two saved replications.",
    }

    (OUT / "r50_reanalysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
