from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from polynomial_dispersion_compiler import PolynomialDispersionCompiler
from r195_benchmark import jsonable, make_dispersion


HERE = Path(__file__).resolve().parent


def spectral_run(
    compiler: PolynomialDispersionCompiler,
    q: float,
    margin: float,
    additive_control: float,
    initial_mode: int,
    *,
    seed: int,
    n_grid: int = 128,
    total_time: float = 55.0,
    dt: float = 0.025,
) -> dict:
    """1D generalized pattern PDE with the supplied polynomial dispersion.

    The linear Fourier symbol is the compiled dispersion and the local cubic
    term saturates growth. Rates are divided by the compiled margin, which only
    changes the time/amplitude units and permits equal-regime comparison.
    """
    rng = np.random.default_rng(seed)
    grid = np.arange(n_grid) / n_grid
    field = 1.15 * np.cos(2 * np.pi * initial_mode * grid)
    field += rng.normal(scale=2e-4, size=n_grid)
    field -= field.mean()

    signed_modes = np.fft.fftfreq(n_grid) * n_grid
    z = signed_modes**2 * q
    linear = np.polynomial.polynomial.polyval(z, compiler.coefficients)
    linear = (linear + additive_control) / margin
    linear[0] = -10.0  # keep the material's mean state fixed at zero
    step = linear * dt
    exp_step = np.exp(np.clip(step, -745.0, 40.0))
    phi = np.where(np.abs(step) < 1e-10, 1.0, np.expm1(np.clip(step, -745.0, 40.0)) / step)

    for _ in range(int(round(total_time / dt))):
        nonlinear_hat = np.fft.fft(-(field**3))
        field_hat = exp_step * np.fft.fft(field) + dt * phi * nonlinear_hat
        field_hat[0] = 0.0
        field = np.fft.ifft(field_hat).real
        if not np.all(np.isfinite(field)) or np.max(np.abs(field)) > 20:
            raise RuntimeError("spectral validation diverged")

    amplitudes = 2.0 * np.abs(np.fft.rfft(field)) / n_grid
    amplitudes[0] = 0.0
    winner = int(np.argmax(amplitudes))
    return {
        "winner": winner,
        "target_amplitudes": amplitudes,
        "field_rms": float(np.sqrt(np.mean(field**2))),
    }


def one_case(seed: int, family: str, target: int, operating_rival_rate: float) -> dict:
    coefficients, peak_z = make_dispersion(seed, family)
    compiler = PolynomialDispersionCompiler(coefficients)
    modes = list(range(1, 17))
    center_q = peak_z / target**2
    design = compiler.design(target, modes, (0.4 * center_q, 2.5 * center_q))
    incumbent = design.rival_mode
    margin = design.separation_margin

    # Under normal operation the incumbent remains linearly unstable. The target
    # has a larger rate but starts from noise behind a saturated incumbent.
    normal_control = -design.base_rival_rate + operating_rival_rate * margin
    normal = spectral_run(
        compiler,
        design.q,
        margin,
        normal_control,
        incumbent,
        seed=seed * 31 + target,
    )
    quench = spectral_run(
        compiler,
        design.q,
        margin,
        design.additive_quench,
        incumbent,
        seed=seed * 31 + target,
    )
    retained = spectral_run(
        compiler,
        design.q,
        margin,
        normal_control,
        target,
        seed=seed * 31 + target + 1,
        total_time=35.0,
    )
    return {
        "seed": seed,
        "family": family,
        "target": target,
        "incumbent": incumbent,
        "operating_rival_rate_over_margin": operating_rival_rate,
        "design": design,
        "normal_winner": normal["winner"],
        "quench_winner": quench["winner"],
        "normal_target_won": normal["winner"] == target,
        "quench_target_won": quench["winner"] == target,
        "normal_incumbent_persisted": normal["winner"] == incumbent,
        "post_quench_target_retained": retained["winner"] == target,
        "normal_target_amplitude": float(normal["target_amplitudes"][target]),
        "quench_target_amplitude": float(quench["target_amplitudes"][target]),
    }


def main():
    started = time.perf_counter()
    cases = []
    operating_rates = (0.2, 0.5, 1.0, 2.0, 3.0, 5.0)
    for seed in range(5):
        for family in ("swift_hohenberg", "thin_film_quartic", "sixth_order_material"):
            for target in (4, 7):
                for operating_rate in operating_rates:
                    cases.append(one_case(seed, family, target, operating_rate))
    by_rate = {}
    for rate in operating_rates:
        group = [c for c in cases if c["operating_rival_rate_over_margin"] == rate]
        by_rate[str(rate)] = {
            "n": len(group),
            "normal_target_wins": sum(c["normal_target_won"] for c in group),
            "normal_incumbent_persists": sum(c["normal_incumbent_persisted"] for c in group),
            "quench_target_wins": sum(c["quench_target_won"] for c in group),
            "post_quench_target_retained": sum(c["post_quench_target_retained"] for c in group),
        }
    summary = {
        "n_cases": len(cases),
        "normal_target_wins": sum(c["normal_target_won"] for c in cases),
        "normal_incumbent_persists": sum(c["normal_incumbent_persisted"] for c in cases),
        "quench_target_wins": sum(c["quench_target_won"] for c in cases),
        "post_quench_target_retained": sum(c["post_quench_target_retained"] for c in cases),
        "median_quench_to_normal_target_amplitude_ratio": float(
            np.median(
                [
                    c["quench_target_amplitude"] / max(c["normal_target_amplitude"], 1e-12)
                    for c in cases
                ]
            )
        ),
        "by_operating_rival_rate_over_margin": by_rate,
    }
    result = {
        "scope": "1D pseudospectral generalized pattern PDE; non-biological polynomial dispersion shell",
        "cases": cases,
        "summary": summary,
        "elapsed_seconds": time.perf_counter() - started,
    }
    (HERE / "PDE_VALIDATION_RESULT.json").write_text(
        json.dumps(jsonable(result), indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print(f"elapsed_seconds={result['elapsed_seconds']:.3f}")


if __name__ == "__main__":
    main()
