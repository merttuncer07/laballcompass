from __future__ import annotations

import copy
import json
import math
import sys
import time
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
R203 = HERE.parent / "R203_PUGACHEV_AUTOMATIC_PSD_ATOM_LANGUAGE"
sys.path.insert(0, str(R203))

from automatic_psd_closure import (  # noqa: E402
    REGIMES,
    chi_radius90,
    compile_closure,
    compiled_sequence,
    ekf_sequence,
    error_radius,
    measurement_noise,
    measurement_variance,
    metrics,
    observation,
    particle_sequence,
    standard_noise,
    transition_matrix,
    ukf_sequence,
)


DIMENSIONS = (2, 4, 8, 16)
DOMAINS = ("home", "parameter_shift", "dense_correlated_shift")


def dense_transition(dimension: int):
    rng = np.random.default_rng(2_040_000 + dimension)
    basis, _ = np.linalg.qr(rng.normal(size=(dimension, dimension)))
    eigenvalues = np.linspace(0.72, 0.94, dimension)
    return basis @ np.diag(eigenvalues) @ basis.T


def domain_parameters(dimension: int, domain: str):
    if domain == "home":
        return transition_matrix(dimension, False), 0.28, 0.16, 0.0
    if domain == "parameter_shift":
        return transition_matrix(dimension, True), 0.33, 0.24, 0.0
    if domain == "dense_correlated_shift":
        return dense_transition(dimension), 0.32, 0.20, 0.32
    raise ValueError(domain)


def shifted_system_paths(
    rng,
    regime,
    trajectories,
    steps,
    transition,
    process_scale,
    cubic,
    measurement_correlation,
):
    dimension = transition.shape[0]
    state = np.zeros((trajectories, steps, dimension))
    state[:, 0] = standard_noise(rng, regime, (trajectories, dimension))
    for step in range(1, steps):
        state[:, step] = (
            state[:, step - 1] @ transition.T
            + process_scale
            * standard_noise(rng, regime, (trajectories, dimension))
        )
    noise = measurement_noise(rng, regime, state.shape)
    if measurement_correlation:
        correlation = (
            (1.0 - measurement_correlation) * np.eye(dimension)
            + measurement_correlation * np.ones((dimension, dimension))
        )
        root = np.linalg.cholesky(correlation)
        noise = np.einsum("...i,ji->...j", noise, root)
    measured = observation(state, cubic) + noise
    return state, measured


def calibrate(closure, regime: str, variant_index: int):
    dimension = closure.dimension
    rng = np.random.default_rng(
        2_140_000 + 101 * dimension + 17 * REGIMES.index(regime) + variant_index
    )
    transition, process_scale, cubic, correlation = domain_parameters(dimension, "home")
    state, measured = shifted_system_paths(
        rng,
        regime,
        160,
        52,
        transition,
        process_scale,
        cubic,
        correlation,
    )
    estimate, covariance = compiled_sequence(
        closure, measured, transition, process_scale, cubic
    )
    radius = error_radius(
        estimate[:, 5:] - state[:, 5:], covariance[:, 5:]
    )
    closure.tail_radius90 = float(np.quantile(radius, 0.90))


def make_variants(closure, regime: str):
    conditional = copy.deepcopy(closure)
    global_atom = copy.deepcopy(closure)
    global_atom.covariance_atoms[:] = np.mean(
        global_atom.covariance_atoms, axis=0
    )
    identity_atom = copy.deepcopy(closure)
    identity_atom.covariance_atoms[:] = np.eye(closure.dimension)
    no_learned_mean = copy.deepcopy(closure)
    no_learned_mean.mean_coefficient[:] = 0.0
    variants = {
        "conditional_atoms": conditional,
        "global_atom": global_atom,
        "identity_atom": identity_atom,
        "no_learned_mean": no_learned_mean,
    }
    for index, variant in enumerate(variants.values()):
        calibrate(variant, regime, index)
    return variants


def run_case(variants, seed, regime, domain):
    dimension = variants["conditional_atoms"].dimension
    transition, process_scale, cubic, correlation = domain_parameters(
        dimension, domain
    )
    rng = np.random.default_rng(
        2_240_000
        + 1009 * dimension
        + 37 * seed
        + 17 * REGIMES.index(regime)
        + 3 * DOMAINS.index(domain)
    )
    state, measured = shifted_system_paths(
        rng,
        regime,
        22,
        58,
        transition,
        process_scale,
        cubic,
        correlation,
    )
    variant_results = {}
    conditional_seconds = None
    for name, closure in variants.items():
        started = time.perf_counter()
        result = compiled_sequence(
            closure, measured, transition, process_scale, cubic
        )
        elapsed = time.perf_counter() - started
        variant_results[name] = metrics(
            *result, state, closure.tail_radius90
        )
        if name == "conditional_atoms":
            conditional_seconds = elapsed

    ekf = ekf_sequence(
        measured,
        transition,
        process_scale,
        cubic,
        measurement_variance(regime),
    )
    ukf = ukf_sequence(
        measured,
        transition,
        process_scale,
        cubic,
        measurement_variance(regime),
    )
    started = time.perf_counter()
    particle = particle_sequence(
        np.random.default_rng(
            2_340_000 + 1009 * dimension + 37 * seed + DOMAINS.index(domain)
        ),
        regime,
        measured,
        transition,
        process_scale,
        cubic,
        count=512,
    )
    particle_seconds = time.perf_counter() - started
    radius = chi_radius90(dimension)
    return {
        "dimension": dimension,
        "seed": seed,
        "regime": regime,
        "domain": domain,
        "measurement_correlation": correlation,
        **variant_results,
        "ekf": metrics(*ekf, state, radius),
        "ukf": metrics(*ukf, state, radius),
        "particle512": metrics(*particle, state, radius),
        "conditional_seconds": conditional_seconds,
        "particle_seconds": particle_seconds,
    }


def average(cases, method, metric):
    return float(np.mean([case[method][metric] for case in cases]))


def run_all():
    closures = {}
    compile_records = []
    for dimension in DIMENSIONS:
        for regime in REGIMES:
            closure, record = compile_closure(dimension, regime)
            closures[(dimension, regime)] = make_variants(closure, regime)
            compile_records.append(record)

    cases = [
        run_case(closures[(dimension, regime)], seed, regime, domain)
        for dimension in DIMENSIONS
        for seed in range(6)
        for regime in REGIMES
        for domain in DOMAINS
    ]
    dimension_summary = {}
    for dimension in DIMENSIONS:
        selected = [case for case in cases if case["dimension"] == dimension]
        home = [case for case in selected if case["domain"] == "home"]
        stress = [case for case in selected if case["domain"] != "home"]
        mixture = [case for case in selected if case["regime"] == "mixture"]
        mixture_home = [
            case
            for case in home
            if case["regime"] == "mixture"
        ]
        compile_record = [
            row for row in compile_records if row["dimension"] == dimension
        ][0]
        dimension_summary[str(dimension)] = {
            "case_count": len(selected),
            "home_conditional_rmse": average(
                home, "conditional_atoms", "rmse_per_coordinate"
            ),
            "home_ukf_rmse": average(home, "ukf", "rmse_per_coordinate"),
            "home_particle_rmse": average(
                home, "particle512", "rmse_per_coordinate"
            ),
            "stress_conditional_rmse": average(
                stress, "conditional_atoms", "rmse_per_coordinate"
            ),
            "stress_ukf_rmse": average(stress, "ukf", "rmse_per_coordinate"),
            "home_coverage90": average(home, "conditional_atoms", "coverage90"),
            "stress_coverage90": average(
                stress, "conditional_atoms", "coverage90"
            ),
            "home_axis_radius90": average(
                home, "conditional_atoms", "mean_axis_radius90"
            ),
            "home_particle_axis_radius90": average(
                home, "particle512", "mean_axis_radius90"
            ),
            "home_global_atom_axis_radius90": average(
                home, "global_atom", "mean_axis_radius90"
            ),
            "mixture_conditional_beats_ukf": int(
                sum(
                    case["conditional_atoms"]["rmse_per_coordinate"]
                    < case["ukf"]["rmse_per_coordinate"]
                    for case in mixture
                )
            ),
            "mixture_case_count": len(mixture),
            "mixture_home_conditional_beats_no_learned_mean": int(
                sum(
                    case["conditional_atoms"]["rmse_per_coordinate"]
                    < case["no_learned_mean"]["rmse_per_coordinate"]
                    for case in mixture_home
                )
            ),
            "mixture_home_case_count": len(mixture_home),
            "home_within_20pct_particle": int(
                sum(
                    case["conditional_atoms"]["rmse_per_coordinate"]
                    <= 1.20 * case["particle512"]["rmse_per_coordinate"]
                    for case in home
                )
            ),
            "home_case_count": len(home),
            "median_speedup_vs_particle512": float(
                np.median(
                    [
                        case["particle_seconds"] / case["conditional_seconds"]
                        for case in selected
                    ]
                )
            ),
            "atom_count": compile_record["atom_count"],
            "model_storage_bytes": compile_record["model_storage_bytes"],
            "atom_storage_reduction": compile_record[
                "atom_storage_reduction"
            ],
            "minimum_covariance_eigenvalue": min(
                case["conditional_atoms"]["minimum_covariance_eigenvalue"]
                for case in selected
            ),
        }

    home_coverage_gate = all(
        0.86 <= row["home_coverage90"] <= 0.94
        for row in dimension_summary.values()
    )
    stress_coverage_gate = all(
        0.78 <= row["stress_coverage90"] <= 0.98
        for row in dimension_summary.values()
    )
    sharpness_gate = all(
        row["home_axis_radius90"]
        <= 1.40 * row["home_particle_axis_radius90"]
        for row in dimension_summary.values()
    )
    approximation_gate = sum(
        row["home_within_20pct_particle"] for row in dimension_summary.values()
    ) >= 40
    mixture_gate = sum(
        row["mixture_conditional_beats_ukf"]
        for row in dimension_summary.values()
    ) >= 60
    mean_ablation_gate = sum(
        row["mixture_home_conditional_beats_no_learned_mean"]
        for row in dimension_summary.values()
    ) >= 20
    atom_ablation_gate = sum(
        row["home_axis_radius90"] <= row["home_global_atom_axis_radius90"]
        for row in dimension_summary.values()
    ) >= 3
    psd_gate = all(
        row["minimum_covariance_eigenvalue"] > 0.0
        for row in dimension_summary.values()
    )
    scaling_gate = (
        dimension_summary["16"]["atom_count"] == 36
        and dimension_summary["16"]["atom_storage_reduction"] > 1e12
    )
    summary = {
        "case_count": len(cases),
        "dimensions": list(DIMENSIONS),
        "domains": list(DOMAINS),
        "home_coverage_gate": home_coverage_gate,
        "stress_coverage_gate": stress_coverage_gate,
        "sharpness_gate": sharpness_gate,
        "particle_approximation_gate": approximation_gate,
        "mixture_ukf_gate": mixture_gate,
        "mean_ablation_gate": mean_ablation_gate,
        "atom_ablation_gate": atom_ablation_gate,
        "psd_gate": psd_gate,
        "scaling_gate": scaling_gate,
        "dimension_summary": dimension_summary,
    }
    summary["status"] = (
        "AUTOMATIC_PSD_CLOSURE_SURVIVES_SECOND_PASS"
        if all(
            (
                home_coverage_gate,
                stress_coverage_gate,
                sharpness_gate,
                approximation_gate,
                mixture_gate,
                mean_ablation_gate,
                atom_ablation_gate,
                psd_gate,
                scaling_gate,
            )
        )
        else "SECOND_PASS_EXPOSES_OPEN_COORDINATE"
    )
    return {"summary": summary, "compile_records": compile_records, "cases": cases}


if __name__ == "__main__":
    started = time.perf_counter()
    result = run_all()
    result["elapsed_seconds"] = time.perf_counter() - started
    path = HERE / "R204_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"elapsed_seconds={result['elapsed_seconds']:.3f}")
    print(f"wrote {path}")
