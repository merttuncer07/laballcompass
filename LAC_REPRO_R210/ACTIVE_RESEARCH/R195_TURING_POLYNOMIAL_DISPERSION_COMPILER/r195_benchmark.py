from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from polynomial_dispersion_compiler import PolynomialDispersionCompiler, simulate_transition


HERE = Path(__file__).resolve().parent


def jsonable(v):
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, (np.floating, np.integer)):
        return v.item()
    if hasattr(v, "__dict__"):
        return jsonable(v.__dict__)
    return v


def make_dispersion(seed: int, family: str):
    rng = np.random.default_rng(seed)
    if family == "swift_hohenberg":
        k0 = rng.uniform(0.65, 1.8)
        return np.array([-k0**4, 2 * k0**2, -1.0]), k0**2
    if family == "thin_film_quartic":
        drive = rng.uniform(0.7, 2.2)
        bending = rng.uniform(0.5, 1.8)
        return np.array([0.0, drive, -bending]), drive / (2 * bending)
    if family == "sixth_order_material":
        drive = rng.uniform(1.0, 2.5)
        quartic = rng.uniform(0.35, 1.1)
        sixth = rng.uniform(0.05, 0.25)
        coefficients = np.array([0.0, drive, -quartic, -sixth])
        derivative = np.array([drive, -2 * quartic, -3 * sixth])
        roots = np.polynomial.polynomial.polyroots(derivative)
        positive = [r.real for r in roots if abs(r.imag) < 1e-10 and r.real > 0]
        return coefficients, float(min(positive))
    raise ValueError(family)


def algebra_vs_grid_case(seed: int, family: str, target: int) -> dict:
    coefficients, peak_z = make_dispersion(seed, family)
    compiler = PolynomialDispersionCompiler(coefficients)
    modes = list(range(1, 17))
    center_q = peak_z / target**2
    q_bounds = (0.35 * center_q, 2.8 * center_q)
    start = time.perf_counter()
    design = compiler.design(target, modes, q_bounds)
    compile_seconds = time.perf_counter() - start
    oracle = compiler.dense_oracle(target, modes, q_bounds, samples=100_001)
    return {
        "seed": seed,
        "family": family,
        "target": target,
        "coefficients": coefficients,
        "q_bounds": q_bounds,
        "design": design,
        "oracle": oracle,
        "margin_regret": float(oracle["margin"] - design.separation_margin),
        "relative_margin_regret": float(
            max(0.0, oracle["margin"] - design.separation_margin)
            / max(abs(oracle["margin"]), 1e-12)
        ),
        "compile_milliseconds": compile_seconds * 1e3,
    }


def dynamic_case(seed: int, family: str, target: int) -> dict:
    coefficients, peak_z = make_dispersion(seed, family)
    compiler = PolynomialDispersionCompiler(coefficients)
    modes = list(range(max(1, target - 4), target + 5))
    center_q = peak_z / target**2
    design = compiler.design(target, modes, (0.4 * center_q, 2.5 * center_q))
    margin = design.separation_margin
    base = {m: float(compiler.modal_rate_q(m, design.q)) for m in modes}
    previous = target - 1

    # Normal operation leaves the strongest rival slightly unstable. Rates are
    # normalized by the compiled margin so different physical coefficients are
    # compared at equal modal-separation time.
    normal_control = -design.base_rival_rate + 0.20 * margin
    normal_rates = {m: (rate + normal_control) / margin for m, rate in base.items()}
    quench_rates = {m: (rate + design.additive_quench) / margin for m, rate in base.items()}
    normal = simulate_transition(normal_rates, previous, target)
    quench = simulate_transition(quench_rates, previous, target)
    # Return to normal control after target capture.
    settle = simulate_transition(
        normal_rates,
        target,
        target,
        hold_time=25.0,
    )
    return {
        "seed": seed,
        "family": family,
        "target": target,
        "previous": previous,
        "design": design,
        "normal_only": normal,
        "compiled_quench": quench,
        "post_quench_settle_from_target": settle,
    }


def summarize(algebra_cases, dynamic_cases):
    return {
        "n_algebra_cases": len(algebra_cases),
        "near_oracle_margin_cases": sum(c["relative_margin_regret"] < 1e-7 for c in algebra_cases),
        "max_relative_margin_regret": float(max(c["relative_margin_regret"] for c in algebra_cases)),
        "median_compile_milliseconds": float(np.median([c["compile_milliseconds"] for c in algebra_cases])),
        "median_candidate_count": float(np.median([c["design"].candidate_count for c in algebra_cases])),
        "all_quenches_sign_separated": all(
            c["design"].target_quench_rate > 0 and c["design"].worst_rival_quench_rate < 0
            for c in algebra_cases
        ),
        "n_dynamic_cases": len(dynamic_cases),
        "normal_target_wins": sum(c["normal_only"]["target_won"] for c in dynamic_cases),
        "quench_target_wins": sum(c["compiled_quench"]["target_won"] for c in dynamic_cases),
        "post_quench_settle_retains_target": sum(
            c["post_quench_settle_from_target"]["target_won"] for c in dynamic_cases
        ),
    }


def main():
    started = time.perf_counter()
    families = ("swift_hohenberg", "thin_film_quartic", "sixth_order_material")
    algebra_cases = []
    for seed in range(12):
        for family in families:
            for target in (3, 5, 8, 12):
                algebra_cases.append(algebra_vs_grid_case(seed, family, target))
    dynamic_cases = []
    for seed in range(10):
        for family in families:
            for target in (4, 6, 9):
                dynamic_cases.append(dynamic_case(seed, family, target))
    result = {
        "round": "R195_TURING_POLYNOMIAL_DISPERSION_COMPILER",
        "algebra_cases": algebra_cases,
        "dynamic_cases": dynamic_cases,
        "summary": summarize(algebra_cases, dynamic_cases),
        "elapsed_seconds": time.perf_counter() - started,
    }
    (HERE / "R195_RESULT.json").write_text(json.dumps(jsonable(result), indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"elapsed_seconds={result['elapsed_seconds']:.3f}")


if __name__ == "__main__":
    main()
