from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from polynomial_dispersion_compiler import PolynomialDispersionCompiler
from r195_benchmark import jsonable, make_dispersion


HERE = Path(__file__).resolve().parent


def perturb_coefficients(coefficients: np.ndarray, noise: float, rng) -> np.ndarray:
    scale = max(float(np.max(np.abs(coefficients))), 1e-6)
    return coefficients + rng.normal(scale=noise * (np.abs(coefficients) + 0.08 * scale))


def one_case(seed: int, family: str, target: int, noise: float) -> dict:
    true_coefficients, peak_z = make_dispersion(seed, family)
    rng = np.random.default_rng(800_000 + seed * 101 + target * 13 + int(noise * 1000))
    estimated = perturb_coefficients(true_coefficients, noise, rng)
    estimated_compiler = PolynomialDispersionCompiler(estimated)
    true_compiler = PolynomialDispersionCompiler(true_coefficients)
    modes = list(range(1, 17))
    center_q = peak_z / target**2
    q_bounds = (0.4 * center_q, 2.5 * center_q)
    def true_metrics(design):
        target_base = float(true_compiler.modal_rate_q(target, design.q))
        rival_bases = {
            mode: float(true_compiler.modal_rate_q(mode, design.q))
            for mode in modes
            if mode != target
        }
        worst_rival = max(rival_bases.values())
        target_rate = target_base + design.additive_quench
        rival_rate = worst_rival + design.additive_quench
        return {
            "target_dominant": target_base > worst_rival,
            "sign_separated": target_rate > 0 and rival_rate < 0,
            "target_rate": target_rate,
            "rival_rate": rival_rate,
            "margin": target_base - worst_rival,
        }

    try:
        point_design = estimated_compiler.design(target, modes, q_bounds)
        point_metrics = true_metrics(point_design)
        point_compiled = True
    except ValueError:
        point_design = None
        point_compiled = False
        point_metrics = {
            "target_dominant": False,
            "sign_separated": False,
            "target_rate": None,
            "rival_rate": None,
            "margin": None,
        }
    scale = max(float(np.max(np.abs(estimated))), 1e-6)
    radius = 3.0 * noise * (np.abs(estimated) + 0.10 * scale)
    lower, upper = estimated - radius, estimated + radius
    true_covered = bool(np.all(true_coefficients >= lower) and np.all(true_coefficients <= upper))
    try:
        robust_design = estimated_compiler.design_interval(
            target, modes, q_bounds, lower, upper
        )
        robust_metrics = true_metrics(robust_design)
        robust_compiled = True
    except ValueError:
        robust_design = None
        robust_metrics = {
            "target_dominant": False,
            "sign_separated": False,
            "target_rate": None,
            "rival_rate": None,
            "margin": None,
        }
        robust_compiled = False

    try:
        shape_design = estimated_compiler.design_shape_interval(
            target, modes, q_bounds, lower, upper
        )
        true_target = float(true_compiler.modal_rate_q(target, shape_design.q))
        true_rivals = {
            mode: float(true_compiler.modal_rate_q(mode, shape_design.q))
            for mode in modes
            if mode != target
        }
        true_rival = max(true_rivals.values())
        probe_bound = 0.40 * shape_design.certified_separation_margin
        target_error = rng.uniform(-probe_bound, probe_bound)
        rival_error = rng.uniform(-probe_bound, probe_bound)
        probe_quench = estimated_compiler.microprobe_quench(
            true_target + target_error, true_rival + rival_error
        )
        shape_compiled = True
        shape_true_dominant = true_target > true_rival
        shape_probe_sign_separated = (
            true_target + probe_quench > 0 and true_rival + probe_quench < 0
        )
    except ValueError:
        shape_design = None
        shape_compiled = False
        shape_true_dominant = False
        shape_probe_sign_separated = False
    return {
        "seed": seed,
        "family": family,
        "target": target,
        "noise": noise,
        "point_compiled": point_compiled,
        "point_true_target_dominant": point_metrics["target_dominant"],
        "point_true_sign_separated": point_metrics["sign_separated"],
        "point_estimated_margin": (
            point_design.separation_margin if point_design is not None else None
        ),
        "point_true_margin": point_metrics["margin"],
        "interval_true_covered": true_covered,
        "robust_compiled": robust_compiled,
        "robust_true_target_dominant": robust_metrics["target_dominant"],
        "robust_true_sign_separated": robust_metrics["sign_separated"],
        "robust_certified_margin": (
            robust_design.separation_margin if robust_design is not None else None
        ),
        "shape_compiled": shape_compiled,
        "shape_true_dominant": shape_true_dominant,
        "shape_probe_sign_separated": shape_probe_sign_separated,
        "shape_certified_margin": (
            shape_design.certified_separation_margin if shape_design is not None else None
        ),
    }


def main():
    cases = []
    noises = (0.0, 0.01, 0.03, 0.05, 0.10, 0.20)
    for seed in range(20):
        for family in ("swift_hohenberg", "thin_film_quartic", "sixth_order_material"):
            for target in (4, 7, 11):
                for noise in noises:
                    cases.append(one_case(seed, family, target, noise))
    by_noise = {}
    for noise in noises:
        group = [c for c in cases if c["noise"] == noise]
        by_noise[str(noise)] = {
            "n": len(group),
            "point_true_target_dominant": sum(c["point_true_target_dominant"] for c in group),
            "point_true_sign_separated": sum(c["point_true_sign_separated"] for c in group),
            "interval_true_covered": sum(c["interval_true_covered"] for c in group),
            "robust_compiled": sum(c["robust_compiled"] for c in group),
            "robust_true_sign_separated": sum(c["robust_true_sign_separated"] for c in group),
            "robust_sign_separated_when_covered_and_compiled": sum(
                c["robust_true_sign_separated"]
                for c in group
                if c["interval_true_covered"] and c["robust_compiled"]
            ),
            "covered_and_compiled": sum(
                c["interval_true_covered"] and c["robust_compiled"] for c in group
            ),
            "shape_compiled": sum(c["shape_compiled"] for c in group),
            "shape_true_dominant": sum(c["shape_true_dominant"] for c in group),
            "shape_probe_sign_separated": sum(
                c["shape_probe_sign_separated"] for c in group
            ),
            "shape_certified_when_covered_and_compiled": sum(
                c["shape_probe_sign_separated"]
                for c in group
                if c["interval_true_covered"] and c["shape_compiled"]
            ),
            "shape_covered_and_compiled": sum(
                c["interval_true_covered"] and c["shape_compiled"] for c in group
            ),
        }
    result = {
        "cases": cases,
        "summary": {"n_cases": len(cases), "by_coefficient_noise": by_noise},
    }
    (HERE / "UNCERTAINTY_VALIDATION_RESULT.json").write_text(
        json.dumps(jsonable(result), indent=2), encoding="utf-8"
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
