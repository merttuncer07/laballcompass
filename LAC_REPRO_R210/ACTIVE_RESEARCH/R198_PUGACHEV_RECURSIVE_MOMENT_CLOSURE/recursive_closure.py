from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
R197 = HERE.parent / "R197_THEORY_BOTTLENECK_PORTFOLIO_WAVE2"
sys.path.insert(0, str(R197))

from theory_wave2 import (  # noqa: E402
    REGIMES,
    _noise_likelihood,
    _noise_variance,
    _sample_noise,
    _standard_prior,
    conditional_basis,
    observation,
    observation_derivative,
    ridge,
    sample_conditional_problem,
)


@dataclass
class RecursiveMomentClosure:
    center: np.ndarray
    spread: np.ndarray
    mean_coefficient: np.ndarray
    second_coefficient: np.ndarray
    variance_calibration: float
    coverage_multiplier90: float
    training_cubic: float
    noise_variance: float

    def update(self, prior_mean, prior_variance, measured, cubic: float):
        prior_scale = np.sqrt(np.maximum(prior_variance, 1e-10))
        basis = conditional_basis(
            np.asarray(prior_mean),
            prior_scale,
            np.asarray(measured),
            cubic,
            self.noise_variance,
        )
        normalized = (basis - self.center) / self.spread
        normalized_mean = normalized @ self.mean_coefficient
        normalized_second = normalized @ self.second_coefficient
        normalized_variance = self.variance_calibration * np.maximum(
            normalized_second - normalized_mean**2, 2e-4
        )
        normalized_variance = np.clip(normalized_variance, 2e-4, 9.0)
        posterior_mean = np.asarray(prior_mean) + prior_scale * normalized_mean
        posterior_variance = np.asarray(prior_variance) * normalized_variance
        return posterior_mean, posterior_variance


def compile_recursive_closure(regime: str, seed: int = 0) -> RecursiveMomentClosure:
    rng = np.random.default_rng(130000 + seed + REGIMES.index(regime))
    mean, scale, measured, state = sample_conditional_problem(
        rng, regime, 90000, cubic=0.18
    )
    basis = conditional_basis(mean, scale, measured, 0.18, _noise_variance(regime))
    center = basis.mean(axis=0)
    spread = np.maximum(basis.std(axis=0), 1e-8)
    center[0], spread[0] = 0.0, 1.0
    normalized = (basis - center) / spread
    error = (state - mean) / scale

    mean_coefficient = ridge(normalized, error, 2e-5)
    first_residual = error - normalized @ mean_coefficient
    robust_scale = np.median(np.abs(first_residual - np.median(first_residual))) / 0.67449
    weights = 1.0 / (1.0 + (first_residual / max(2.5 * robust_scale, 1e-6)) ** 2)
    mean_coefficient = ridge(normalized, error, 2e-5, weights)
    second_coefficient = ridge(normalized, error**2, 8e-5)

    predicted_mean = normalized @ mean_coefficient
    predicted_second = normalized @ second_coefficient
    raw_variance = np.maximum(predicted_second - predicted_mean**2, 2e-4)
    squared_residual = (error - predicted_mean) ** 2
    mse_calibration = float(np.mean(squared_residual) / np.mean(raw_variance))
    standardized = np.abs(error - predicted_mean) / np.sqrt(raw_variance)
    calibration = mse_calibration
    coverage_multiplier90 = float(np.quantile(standardized, 0.90))
    closure = RecursiveMomentClosure(
        center,
        spread,
        mean_coefficient,
        second_coefficient,
        calibration,
        coverage_multiplier90,
        0.18,
        _noise_variance(regime),
    )
    calibration_rng = np.random.default_rng(150000 + seed + REGIMES.index(regime))
    calibration_state, calibration_measured = _system_paths(
        calibration_rng,
        regime,
        trajectories=160,
        steps=65,
        transition=0.82,
        process_scale=0.36,
        cubic=0.18,
    )
    calibration_mean, calibration_variance = _compiled_sequence(
        closure,
        calibration_measured,
        transition=0.82,
        process_scale=0.36,
        cubic=0.18,
    )
    recursive_standardized = np.abs(calibration_mean[:, 5:] - calibration_state[:, 5:])
    recursive_standardized /= np.sqrt(np.maximum(calibration_variance[:, 5:], 1e-10))
    closure.coverage_multiplier90 = float(np.quantile(recursive_standardized, 0.90))
    return closure


def _system_paths(
    rng: np.random.Generator,
    regime: str,
    trajectories: int,
    steps: int,
    transition: float,
    process_scale: float,
    cubic: float,
):
    state = np.zeros((trajectories, steps))
    state[:, 0] = _standard_prior(rng, regime, trajectories)
    for t in range(1, steps):
        state[:, t] = (
            transition * state[:, t - 1]
            + process_scale * _standard_prior(rng, regime, trajectories)
        )
    measured = observation(state, cubic) + _sample_noise(rng, regime, state.shape)
    return state, measured


def _ekf_sequence(measured, transition, process_scale, cubic, noise_variance):
    trajectories, steps = measured.shape
    mean = np.zeros(trajectories)
    variance = np.ones(trajectories)
    estimates = np.zeros_like(measured)
    variances = np.zeros_like(measured)
    for t in range(steps):
        if t > 0:
            mean = transition * mean
            variance = transition**2 * variance + process_scale**2
        slope = observation_derivative(mean, cubic)
        gain = variance * slope / (slope**2 * variance + noise_variance)
        mean = mean + gain * (measured[:, t] - observation(mean, cubic))
        variance = np.maximum(variance * (1.0 - gain * slope), 1e-8)
        estimates[:, t], variances[:, t] = mean, variance
    return estimates, variances


def _ukf_sequence(measured, transition, process_scale, cubic, noise_variance):
    trajectories, steps = measured.shape
    mean = np.zeros(trajectories)
    variance = np.ones(trajectories)
    estimates = np.zeros_like(measured)
    variances = np.zeros_like(measured)
    weights = np.array([2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0])
    for t in range(steps):
        if t > 0:
            mean = transition * mean
            variance = transition**2 * variance + process_scale**2
        scale = np.sqrt(np.maximum(variance, 1e-10))
        points = np.column_stack([mean, mean + math.sqrt(3.0) * scale, mean - math.sqrt(3.0) * scale])
        observed_points = observation(points, cubic)
        observed_mean = observed_points @ weights
        dz = observed_points - observed_mean[:, None]
        dx = points - mean[:, None]
        cross = np.sum(weights[None, :] * dx * dz, axis=1)
        observed_variance = np.sum(weights[None, :] * dz**2, axis=1) + noise_variance
        gain = cross / np.maximum(observed_variance, 1e-12)
        mean = mean + gain * (measured[:, t] - observed_mean)
        variance = np.maximum(variance - gain**2 * observed_variance, 1e-8)
        estimates[:, t], variances[:, t] = mean, variance
    return estimates, variances


def _compiled_sequence(
    closure: RecursiveMomentClosure,
    measured,
    transition,
    process_scale,
    cubic,
):
    trajectories, steps = measured.shape
    mean = np.zeros(trajectories)
    variance = np.ones(trajectories)
    estimates = np.zeros_like(measured)
    variances = np.zeros_like(measured)
    for t in range(steps):
        if t > 0:
            mean = transition * mean
            variance = transition**2 * variance + process_scale**2
        mean, variance = closure.update(mean, variance, measured[:, t], cubic)
        estimates[:, t], variances[:, t] = mean, variance
    return estimates, variances


def _systematic_indices(rng: np.random.Generator, weights: np.ndarray):
    particles = weights.shape[1]
    targets = (rng.random((len(weights), 1)) + np.arange(particles)[None, :]) / particles
    cdf = np.cumsum(weights, axis=1)
    result = np.empty_like(targets, dtype=int)
    for row in range(len(weights)):
        result[row] = np.searchsorted(cdf[row], targets[row], side="right")
    return np.minimum(result, particles - 1)


def _particle_sequence(
    rng: np.random.Generator,
    regime: str,
    measured,
    transition,
    process_scale,
    cubic,
    particles_count: int = 512,
):
    trajectories, steps = measured.shape
    particles = _standard_prior(rng, regime, (trajectories, particles_count))
    estimates = np.zeros_like(measured)
    variances = np.zeros_like(measured)
    for t in range(steps):
        if t > 0:
            particles = transition * particles + process_scale * _standard_prior(
                rng, regime, particles.shape
            )
        likelihood = _noise_likelihood(
            measured[:, t, None] - observation(particles, cubic), regime
        )
        weights = likelihood / np.maximum(likelihood.sum(axis=1, keepdims=True), 1e-300)
        mean = np.sum(weights * particles, axis=1)
        variance = np.sum(weights * (particles - mean[:, None]) ** 2, axis=1)
        estimates[:, t], variances[:, t] = mean, variance
        indices = _systematic_indices(rng, weights)
        particles = np.take_along_axis(particles, indices, axis=1)
    return estimates, np.maximum(variances, 1e-8)


def _metrics(estimate, variance, state, interval_multiplier: float = 1.644854):
    burn = 5
    error = estimate[:, burn:] - state[:, burn:]
    active_variance = np.maximum(variance[:, burn:], 1e-8)
    rmse = float(np.sqrt(np.mean(error**2)))
    coverage90 = float(np.mean(np.abs(error) <= interval_multiplier * np.sqrt(active_variance)))
    nll = float(np.mean(0.5 * (np.log(2.0 * math.pi * active_variance) + error**2 / active_variance)))
    return {"rmse": rmse, "coverage90": coverage90, "gaussian_nll": nll}


def recursive_trial(
    closure: RecursiveMomentClosure,
    seed: int,
    regime: str,
    shifted: bool,
):
    rng = np.random.default_rng(170000 + seed + 101 * REGIMES.index(regime) + int(shifted))
    transition = 0.90 if shifted else 0.82
    cubic = 0.24 if shifted else 0.18
    process_scale = 0.36
    state, measured = _system_paths(
        rng, regime, 70, 65, transition, process_scale, cubic
    )
    start = time.perf_counter()
    compiled = _compiled_sequence(closure, measured, transition, process_scale, cubic)
    compiled_time = time.perf_counter() - start
    ekf = _ekf_sequence(
        measured, transition, process_scale, cubic, _noise_variance(regime)
    )
    ukf = _ukf_sequence(
        measured, transition, process_scale, cubic, _noise_variance(regime)
    )
    start = time.perf_counter()
    particle = _particle_sequence(
        np.random.default_rng(230000 + seed),
        regime,
        measured,
        transition,
        process_scale,
        cubic,
    )
    particle_time = time.perf_counter() - start
    return {
        "seed": seed,
        "regime": regime,
        "shifted": shifted,
        "compiled": _metrics(*compiled, state, interval_multiplier=closure.coverage_multiplier90),
        "ekf": _metrics(*ekf, state),
        "ukf": _metrics(*ukf, state),
        "particle512": _metrics(*particle, state),
        "compiled_seconds": compiled_time,
        "particle_seconds": particle_time,
    }


def run_all():
    closures = {regime: compile_recursive_closure(regime) for regime in REGIMES}
    cases = [
        recursive_trial(closures[regime], seed, regime, shifted)
        for seed in range(5)
        for regime in REGIMES
        for shifted in (False, True)
    ]
    home = [c for c in cases if not c["shifted"]]
    non_gaussian = [c for c in home if c["regime"] != "gaussian"]
    shifted = [c for c in cases if c["shifted"]]
    summary = {
        "case_count": len(cases),
        "home_non_gaussian_compiled_beats_ukf": sum(
            c["compiled"]["rmse"] < c["ukf"]["rmse"] for c in non_gaussian
        ),
        "home_non_gaussian_compiled_beats_ekf": sum(
            c["compiled"]["rmse"] < c["ekf"]["rmse"] for c in non_gaussian
        ),
        "home_compiled_within_15pct_particle": sum(
            c["compiled"]["rmse"] <= 1.15 * c["particle512"]["rmse"] for c in home
        ),
        "shifted_compiled_beats_ukf": sum(
            c["compiled"]["rmse"] < c["ukf"]["rmse"] for c in shifted
        ),
        "mean_home_compiled_rmse": float(np.mean([c["compiled"]["rmse"] for c in home])),
        "mean_home_ukf_rmse": float(np.mean([c["ukf"]["rmse"] for c in home])),
        "mean_home_particle_rmse": float(np.mean([c["particle512"]["rmse"] for c in home])),
        "mean_home_compiled_coverage90": float(
            np.mean([c["compiled"]["coverage90"] for c in home])
        ),
        "median_speedup_vs_particle512": float(
            np.median([c["particle_seconds"] / c["compiled_seconds"] for c in cases])
        ),
    }
    summary["status"] = (
        "RECURSIVE_CONDITIONAL_MEAN_AND_CALIBRATED_SCALE_SURVIVE_NON_GAUSSIAN_FILTERING"
        if summary["home_non_gaussian_compiled_beats_ukf"] >= 8
        and summary["home_compiled_within_15pct_particle"] >= 12
        and 0.86 <= summary["mean_home_compiled_coverage90"] <= 0.94
        else "RECURSIVE_CLOSURE_NOT_BROKEN"
    )
    return {"summary": summary, "cases": cases}


if __name__ == "__main__":
    started = time.perf_counter()
    result = run_all()
    result["elapsed_seconds"] = time.perf_counter() - started
    path = HERE / "R198_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"wrote {path}")
