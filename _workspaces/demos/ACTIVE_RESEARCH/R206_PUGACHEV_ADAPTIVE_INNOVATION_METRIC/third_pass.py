from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
R203 = HERE.parent / "R203_PUGACHEV_AUTOMATIC_PSD_ATOM_LANGUAGE"
R204 = HERE.parent / "R204_PUGACHEV_PSD_CLOSURE_STRESS"
sys.path[:0] = [str(R203), str(R204)]

from automatic_psd_closure import (  # noqa: E402
    REGIMES,
    compile_closure,
    compiled_sequence,
    error_radius,
    measurement_variance,
    transition_matrix,
)
from stress_suite import dense_transition  # noqa: E402

from adaptive_metric import (  # noqa: E402
    AdaptationConfig,
    adaptive_compiled_sequence,
    compound_correlation,
    correlated_system_paths,
    correlation_error,
    fixed_metric_sequence,
    signed_rank_one_correlation,
    ukf_metric_sequence,
)


DIMENSIONS = (2, 4, 8, 16)
SCENARIOS = (
    "home_independent",
    "dense_equicorrelation",
    "strong_equicorrelation",
    "signed_rank_one",
)


def scenario_parameters(dimension: int, name: str):
    if name == "home_independent":
        return transition_matrix(dimension, False), 0.28, 0.16, np.eye(dimension)
    if name == "dense_equicorrelation":
        return (
            dense_transition(dimension),
            0.32,
            0.20,
            compound_correlation(dimension, 0.32),
        )
    if name == "strong_equicorrelation":
        return (
            dense_transition(dimension),
            0.35,
            0.24,
            compound_correlation(dimension, 0.55),
        )
    if name == "signed_rank_one":
        return (
            dense_transition(dimension),
            0.32,
            0.20,
            signed_rank_one_correlation(dimension, 0.38),
        )
    raise ValueError(name)


def scored_metrics(estimate, covariance, state, tail_radius, burn=15):
    dimension = state.shape[-1]
    error = estimate[:, burn:] - state[:, burn:]
    active_covariance = covariance[:, burn:]
    radius = error_radius(error, active_covariance)
    axis = tail_radius * np.sqrt(
        np.trace(active_covariance, axis1=-2, axis2=-1) / dimension
    )
    return {
        "rmse_per_coordinate": float(np.sqrt(np.mean(error**2))),
        "coverage90": float(np.mean(radius <= tail_radius)),
        "mean_axis_radius90": float(np.mean(axis)),
        "minimum_covariance_eigenvalue": float(
            np.min(
                np.linalg.eigvalsh(
                    active_covariance.reshape(-1, dimension, dimension)
                )
            )
        ),
    }


def run_case(closure, seed: int, regime: str, scenario: str):
    dimension = closure.dimension
    transition, process_scale, cubic, correlation = scenario_parameters(
        dimension, scenario
    )
    rng = np.random.default_rng(
        2_460_000
        + 1009 * dimension
        + 43 * seed
        + 17 * REGIMES.index(regime)
        + SCENARIOS.index(scenario)
    )
    state, measured = correlated_system_paths(
        rng,
        regime,
        trajectories=20,
        steps=70,
        transition=transition,
        process_scale=process_scale,
        cubic=cubic,
        correlation=correlation,
    )
    variance = measurement_variance(regime)
    truth = variance * correlation
    outputs = {}

    outputs["diagonal"] = compiled_sequence(
        closure, measured, transition, process_scale, cubic
    )
    outputs["oracle"] = fixed_metric_sequence(
        closure, measured, transition, process_scale, cubic, truth
    )
    compound = adaptive_compiled_sequence(
        closure,
        measured,
        transition,
        process_scale,
        cubic,
        AdaptationConfig(
            "compound",
            gain=0.08,
            shrinkage=0.82,
            moment_clip=4.0,
            activation_threshold=0.06,
        ),
    )
    full_local = adaptive_compiled_sequence(
        closure,
        measured,
        transition,
        process_scale,
        cubic,
        AdaptationConfig(
            "full",
            gain=0.055,
            shrinkage=0.68,
            moment_clip=4.0,
            activation_threshold=0.25,
        ),
    )
    full_shared = adaptive_compiled_sequence(
        closure,
        measured,
        transition,
        process_scale,
        cubic,
        AdaptationConfig(
            "full",
            gain=0.11,
            shrinkage=0.86,
            moment_clip=4.0,
            shared_across_batch=True,
            activation_threshold=0.08,
        ),
    )
    outputs["adaptive_compound"] = compound[:2]
    outputs["adaptive_full_local"] = full_local[:2]
    outputs["adaptive_full_shared"] = full_shared[:2]
    outputs["ukf_diagonal"] = ukf_metric_sequence(
        measured,
        transition,
        process_scale,
        cubic,
        variance * np.eye(dimension),
    )
    outputs["ukf_oracle"] = ukf_metric_sequence(
        measured, transition, process_scale, cubic, truth
    )
    result = {
        "dimension": dimension,
        "seed": seed,
        "regime": regime,
        "scenario": scenario,
        "truth_minimum_correlation_eigenvalue": float(
            np.min(np.linalg.eigvalsh(correlation))
        ),
    }
    for name, output in outputs.items():
        result[name] = scored_metrics(
            *output, state, closure.tail_radius90
        )
    result["adaptive_compound"]["correlation_rmse"] = correlation_error(
        compound[2], correlation
    )
    result["adaptive_compound"]["diagnostics"] = compound[3]
    result["adaptive_full_local"]["correlation_rmse"] = correlation_error(
        full_local[2], correlation
    )
    result["adaptive_full_local"]["diagnostics"] = full_local[3]
    result["adaptive_full_shared"]["correlation_rmse"] = correlation_error(
        full_shared[2], correlation
    )
    result["adaptive_full_shared"]["diagnostics"] = full_shared[3]
    return result


def mean(cases, method, metric):
    return float(np.mean([case[method][metric] for case in cases]))


def summarize(cases):
    cells = {}
    for dimension in DIMENSIONS:
        for scenario in SCENARIOS:
            selected = [
                case
                for case in cases
                if case["dimension"] == dimension
                and case["scenario"] == scenario
            ]
            key = f"d{dimension}:{scenario}"
            cell = {"case_count": len(selected)}
            for method in (
                "diagonal",
                "adaptive_compound",
                "adaptive_full_local",
                "adaptive_full_shared",
                "oracle",
                "ukf_diagonal",
                "ukf_oracle",
            ):
                cell[method] = {
                    "rmse": mean(selected, method, "rmse_per_coordinate"),
                    "coverage90": mean(selected, method, "coverage90"),
                    "axis90": mean(selected, method, "mean_axis_radius90"),
                    **(
                        {
                            "correlation_rmse": mean(
                                selected, method, "correlation_rmse"
                            )
                        }
                        if method.startswith("adaptive")
                        else {}
                    ),
                }
            cells[key] = cell

    independent = [c for c in cases if c["scenario"] == "home_independent"]
    equicorrelated = [
        c
        for c in cases
        if c["scenario"]
        in ("dense_equicorrelation", "strong_equicorrelation")
    ]
    signed = [c for c in cases if c["scenario"] == "signed_rank_one"]
    methods = (
        "diagonal",
        "adaptive_compound",
        "adaptive_full_local",
        "adaptive_full_shared",
        "oracle",
    )
    aggregate = {}
    for label, selected in (
        ("independent", independent),
        ("equicorrelated", equicorrelated),
        ("signed_rank_one", signed),
    ):
        aggregate[label] = {
            method: {
                "rmse": mean(selected, method, "rmse_per_coordinate"),
                "coverage90": mean(selected, method, "coverage90"),
                "axis90": mean(selected, method, "mean_axis_radius90"),
            }
            for method in methods
        }
    return {"case_count": len(cases), "aggregate": aggregate, "cells": cells}


def unsafe_anchor_failure_probe(closure):
    """Reproduce the exact strong-cubic overshoot that motivated the ray gate."""
    dimension = 16
    regime = "gaussian"
    scenario = "strong_equicorrelation"
    seed = 2
    transition, process_scale, cubic, correlation = scenario_parameters(
        dimension, scenario
    )
    rng = np.random.default_rng(
        2_460_000
        + 1009 * dimension
        + 43 * seed
        + SCENARIOS.index(scenario)
    )
    state, measured = correlated_system_paths(
        rng,
        regime,
        trajectories=20,
        steps=70,
        transition=transition,
        process_scale=process_scale,
        cubic=cubic,
        correlation=correlation,
    )
    metric = measurement_variance(regime) * correlation
    unsafe = {"failed": False, "failure_type": None}
    try:
        estimate, covariance = fixed_metric_sequence(
            closure,
            measured,
            transition,
            process_scale,
            cubic,
            metric,
            support_gate=False,
        )
        unsafe["failed"] = not (
            np.all(np.isfinite(estimate)) and np.all(np.isfinite(covariance))
        )
        if unsafe["failed"]:
            unsafe["failure_type"] = "nonfinite_state_or_covariance"
    except (FloatingPointError, np.linalg.LinAlgError) as error:
        unsafe = {"failed": True, "failure_type": type(error).__name__}

    safe_estimate, safe_covariance, diagnostics = fixed_metric_sequence(
        closure,
        measured,
        transition,
        process_scale,
        cubic,
        metric,
        support_gate=True,
        return_diagnostics=True,
    )
    safe = scored_metrics(
        safe_estimate, safe_covariance, state, closure.tail_radius90
    )
    safe["all_finite"] = bool(
        np.all(np.isfinite(safe_estimate))
        and np.all(np.isfinite(safe_covariance))
    )
    safe["diagnostics"] = diagnostics
    return {"unsafe": unsafe, "bounded_ray_and_support_gate": safe}


def run_all(seeds=range(4)):
    closures = {
        (dimension, regime): compile_closure(dimension, regime)[0]
        for dimension in DIMENSIONS
        for regime in REGIMES
    }
    cases = []
    for dimension in DIMENSIONS:
        for seed in seeds:
            for regime in REGIMES:
                for scenario in SCENARIOS:
                    print(
                        f"case d={dimension} seed={seed} "
                        f"regime={regime} scenario={scenario}",
                        flush=True,
                    )
                    cases.append(
                        run_case(
                            closures[(dimension, regime)],
                            seed,
                            regime,
                            scenario,
                        )
                    )
    summary = summarize(cases)
    failure_probe = unsafe_anchor_failure_probe(closures[(16, "gaussian")])
    summary["unsafe_anchor_failure_reproduced"] = failure_probe["unsafe"][
        "failed"
    ]
    return {
        "summary": summary,
        "failure_boundary": failure_probe,
        "cases": cases,
    }


if __name__ == "__main__":
    started = time.perf_counter()
    seed_count = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    result = run_all(range(seed_count))
    result["elapsed_seconds"] = time.perf_counter() - started
    path = HERE / (
        "R206_RESULT.json" if seed_count >= 4 else "R206_PROBE_RESULT.json"
    )
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"]["aggregate"], indent=2))
    print(f"elapsed_seconds={result['elapsed_seconds']:.3f}")
    print(f"wrote {path}")
