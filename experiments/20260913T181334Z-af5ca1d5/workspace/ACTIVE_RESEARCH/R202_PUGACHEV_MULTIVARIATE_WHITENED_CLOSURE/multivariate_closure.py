from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REGIMES = ("gaussian", "mixture")


def ridge(x: np.ndarray, y: np.ndarray, lam: float, weights=None):
    if weights is not None:
        root = np.sqrt(weights)[:, None]
        x = x * root
        y = y * root
    gram = x.T @ x
    scale = float(np.trace(gram)) / max(1, gram.shape[0])
    return np.linalg.solve(
        gram + lam * max(scale, 1e-12) * np.eye(gram.shape[0]), x.T @ y
    )


def observation(state: np.ndarray, cubic: float):
    x0, x1 = state[..., 0], state[..., 1]
    return np.stack(
        [
            x0 + cubic * x0**3 + 0.15 * x0 * x1,
            x1 + 0.16 * x1**3 - 0.12 * x0**2,
        ],
        axis=-1,
    )


def jacobian(state: np.ndarray, cubic: float):
    x0, x1 = state[..., 0], state[..., 1]
    result = np.empty(state.shape[:-1] + (2, 2))
    result[..., 0, 0] = 1.0 + 3.0 * cubic * x0**2 + 0.15 * x1
    result[..., 0, 1] = 0.15 * x0
    result[..., 1, 0] = -0.24 * x0
    result[..., 1, 1] = 1.0 + 0.48 * x1**2
    return result


def standard_noise(rng: np.random.Generator, regime: str, shape):
    if regime == "gaussian":
        return rng.normal(size=shape)
    sign = rng.choice(np.array([-1.0, 1.0]), size=shape)
    raw = 0.82 * sign + rng.normal(scale=0.46, size=shape)
    return raw / math.sqrt(0.82**2 + 0.46**2)


def measurement_noise(rng: np.random.Generator, regime: str, shape):
    if regime == "gaussian":
        return rng.normal(scale=0.28, size=shape)
    outlier = rng.random(shape) < 0.10
    result = rng.normal(scale=0.20, size=shape)
    result[outlier] = rng.normal(scale=1.25, size=int(np.sum(outlier)))
    return result


def measurement_variance(regime: str):
    if regime == "gaussian":
        return 0.28**2
    return 0.90 * 0.20**2 + 0.10 * 1.25**2


def measurement_likelihood(residual: np.ndarray, regime: str):
    def normal(value, sigma):
        return np.exp(-0.5 * (value / sigma) ** 2) / (math.sqrt(2.0 * math.pi) * sigma)

    if regime == "gaussian":
        density = normal(residual, 0.28)
    else:
        density = 0.90 * normal(residual, 0.20) + 0.10 * normal(residual, 1.25)
    return np.prod(density, axis=-1)


def random_covariance(rng: np.random.Generator, count: int):
    s0 = np.exp(rng.uniform(math.log(0.25), math.log(1.0), count))
    s1 = np.exp(rng.uniform(math.log(0.25), math.log(1.0), count))
    rho = rng.uniform(-0.55, 0.55, count)
    covariance = np.empty((count, 2, 2))
    covariance[:, 0, 0] = s0**2
    covariance[:, 1, 1] = s1**2
    covariance[:, 0, 1] = covariance[:, 1, 0] = rho * s0 * s1
    return covariance


def sample_training_problem(rng, regime: str, count: int, cubic: float = 0.18):
    mean = rng.uniform(-1.25, 1.25, size=(count, 2))
    covariance = random_covariance(rng, count)
    root = np.linalg.cholesky(covariance)
    standardized = standard_noise(rng, regime, (count, 2))
    state = mean + np.einsum("nij,nj->ni", root, standardized)
    measured = observation(state, cubic) + measurement_noise(rng, regime, state.shape)
    return mean, covariance, measured, state


def conditional_features(mean, covariance, measured, cubic: float, noise_variance: float):
    root = np.linalg.cholesky(covariance)
    derivative = jacobian(mean, cubic)
    innovation_covariance = np.einsum(
        "nij,njk,nlk->nil", derivative, covariance, derivative
    )
    innovation_covariance += noise_variance * np.eye(2)[None, :, :]
    innovation_root = np.linalg.cholesky(innovation_covariance)
    innovation = measured - observation(mean, cubic)
    residual = np.linalg.solve(innovation_root, innovation[..., None])[..., 0]
    residual = np.clip(residual, -6.0, 6.0)
    log_scale = np.log(np.maximum(np.stack([root[:, 0, 0], root[:, 1, 1]], axis=1), 1e-8))
    correlation_coordinate = (root[:, 1, 0] / np.maximum(root[:, 0, 0], 1e-8))[:, None]
    r0, r1 = residual[:, 0], residual[:, 1]
    features = np.column_stack(
        [
            np.ones(len(mean)),
            mean,
            log_scale,
            correlation_coordinate,
            residual,
            r0**2,
            r0 * r1,
            r1**2,
            r0**3,
            r1**3,
            np.tanh(residual),
            mean[:, 0] * r0,
            mean[:, 0] * r1,
            mean[:, 1] * r0,
            mean[:, 1] * r1,
            log_scale[:, 0] * r0,
            log_scale[:, 1] * r1,
            derivative.reshape(len(mean), 4),
        ]
    )
    return features, root


def project_psd(matrix: np.ndarray, floor: float = 2e-4, ceiling: float = 8.0):
    values, vectors = np.linalg.eigh((matrix + np.swapaxes(matrix, -1, -2)) / 2.0)
    values = np.clip(values, floor, ceiling)
    return np.einsum("nij,nj,nkj->nik", vectors, values, vectors)


@dataclass
class MultivariateClosure:
    center: np.ndarray
    spread: np.ndarray
    mean_coefficient: np.ndarray
    covariance_edges: np.ndarray
    covariance_atoms: np.ndarray
    covariance_calibration: float
    tail_radius90: float
    noise_variance: float

    def update(self, prior_mean, prior_covariance, measured, cubic: float):
        features, root = conditional_features(
            prior_mean, prior_covariance, measured, cubic, self.noise_variance
        )
        normalized = (features - self.center) / self.spread
        correction = normalized @ self.mean_coefficient
        # A linear second-moment fit followed by subtraction of the squared
        # conditional mean is numerically fragile under recursion.  Compile a
        # small PSD dictionary instead: each innovation cell stores a shrunk
        # residual outer product, so every deployed covariance is PSD by
        # construction and no cancellation is needed.
        innovation = features[:, 6:8]
        cell0 = np.digitize(innovation[:, 0], self.covariance_edges)
        cell1 = np.digitize(innovation[:, 1], self.covariance_edges)
        normalized_covariance = self.covariance_atoms[cell0, cell1]
        normalized_covariance *= self.covariance_calibration
        posterior_mean = prior_mean + np.einsum("nij,nj->ni", root, correction)
        posterior_covariance = np.einsum(
            "nij,njk,nlk->nil", root, normalized_covariance, root
        )
        return posterior_mean, posterior_covariance


def compile_closure(regime: str, seed: int = 0):
    rng = np.random.default_rng(710000 + seed + REGIMES.index(regime))
    mean, covariance, measured, state = sample_training_problem(rng, regime, 100_000)
    features, root = conditional_features(
        mean, covariance, measured, 0.18, measurement_variance(regime)
    )
    center = features.mean(axis=0)
    spread = np.maximum(features.std(axis=0), 1e-8)
    center[0], spread[0] = 0.0, 1.0
    normalized = (features - center) / spread
    standardized = np.linalg.solve(root, (state - mean)[..., None])[..., 0]
    mean_coefficient = ridge(normalized, standardized, 3e-5)
    residual = standardized - normalized @ mean_coefficient
    scale = np.median(np.linalg.norm(residual, axis=1)) / math.sqrt(2.0 * math.log(2.0))
    robust_weight = 1.0 / (1.0 + (np.linalg.norm(residual, axis=1) / max(2.8 * scale, 1e-6)) ** 2)
    mean_coefficient = ridge(normalized, standardized, 3e-5, robust_weight)
    predicted_mean = normalized @ mean_coefficient
    residual = standardized - predicted_mean
    global_covariance = project_psd((residual.T @ residual / len(residual))[None])[0]
    covariance_edges = np.array([-2.0, -1.25, -0.75, -0.35, 0.0, 0.35, 0.75, 1.25, 2.0])
    cell0 = np.digitize(features[:, 6], covariance_edges)
    cell1 = np.digitize(features[:, 7], covariance_edges)
    cell_count = len(covariance_edges) + 1
    covariance_atoms = np.empty((cell_count, cell_count, 2, 2))
    shrinkage = 180.0
    for i in range(cell_count):
        for j in range(cell_count):
            selected = residual[(cell0 == i) & (cell1 == j)]
            scatter = selected.T @ selected if len(selected) else np.zeros((2, 2))
            covariance_atoms[i, j] = (
                scatter + shrinkage * global_covariance
            ) / (len(selected) + shrinkage)
    covariance_atoms = project_psd(covariance_atoms.reshape(-1, 2, 2)).reshape(
        cell_count, cell_count, 2, 2
    )
    calibration = 1.0
    closure = MultivariateClosure(
        center,
        spread,
        mean_coefficient,
        covariance_edges,
        covariance_atoms,
        calibration,
        math.sqrt(4.605170),
        measurement_variance(regime),
    )
    calibration_rng = np.random.default_rng(760000 + seed + REGIMES.index(regime))
    state_path, measured_path = system_paths(
        calibration_rng, regime, 180, 55, transition_matrix(False), 0.30, 0.18
    )
    estimate, posterior_covariance = compiled_sequence(
        closure, measured_path, transition_matrix(False), 0.30, 0.18
    )
    mahalanobis = error_radius(
        estimate[:, 5:] - state_path[:, 5:], posterior_covariance[:, 5:]
    )
    closure.tail_radius90 = float(np.quantile(mahalanobis, 0.90))
    return closure


def transition_matrix(shifted: bool):
    if shifted:
        return np.array([[0.90, 0.16], [-0.11, 0.91]])
    return np.array([[0.82, 0.12], [-0.08, 0.87]])


def system_paths(rng, regime, trajectories, steps, transition, process_scale, cubic):
    state = np.zeros((trajectories, steps, 2))
    state[:, 0] = standard_noise(rng, regime, (trajectories, 2))
    for t in range(1, steps):
        state[:, t] = state[:, t - 1] @ transition.T + process_scale * standard_noise(
            rng, regime, (trajectories, 2)
        )
    measured = observation(state, cubic) + measurement_noise(rng, regime, state.shape)
    return state, measured


def ensure_psd(matrix, floor=1e-8):
    return project_psd(matrix, floor=floor, ceiling=100.0)


def compiled_sequence(closure, measured, transition, process_scale, cubic):
    trajectories, steps, _ = measured.shape
    mean = np.zeros((trajectories, 2))
    covariance = np.repeat(np.eye(2)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, 2, 2))
    q = process_scale**2 * np.eye(2)
    for t in range(steps):
        if t > 0:
            mean = mean @ transition.T
            covariance = np.einsum("ij,njk,lk->nil", transition, covariance, transition) + q
        mean, covariance = closure.update(mean, covariance, measured[:, t], cubic)
        estimates[:, t], covariances[:, t] = mean, covariance
    return estimates, covariances


def ekf_sequence(measured, transition, process_scale, cubic, noise_variance):
    trajectories, steps, _ = measured.shape
    mean = np.zeros((trajectories, 2))
    covariance = np.repeat(np.eye(2)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, 2, 2))
    q = process_scale**2 * np.eye(2)
    r = noise_variance * np.eye(2)
    identity = np.eye(2)[None, :, :]
    for t in range(steps):
        if t > 0:
            mean = mean @ transition.T
            covariance = np.einsum("ij,njk,lk->nil", transition, covariance, transition) + q
        derivative = jacobian(mean, cubic)
        innovation_covariance = np.einsum(
            "nij,njk,nlk->nil", derivative, covariance, derivative
        ) + r
        gain = np.einsum(
            "nij,nkj,nkl->nil",
            covariance,
            derivative,
            np.linalg.inv(innovation_covariance),
        )
        innovation = measured[:, t] - observation(mean, cubic)
        mean = mean + np.einsum("nij,nj->ni", gain, innovation)
        kh = np.einsum("nij,njk->nik", gain, derivative)
        covariance = np.einsum("nij,njk->nik", identity - kh, covariance)
        covariance = ensure_psd(covariance)
        estimates[:, t], covariances[:, t] = mean, covariance
    return estimates, covariances


def ukf_sequence(measured, transition, process_scale, cubic, noise_variance):
    trajectories, steps, _ = measured.shape
    mean = np.zeros((trajectories, 2))
    covariance = np.repeat(np.eye(2)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, 2, 2))
    q = process_scale**2 * np.eye(2)
    weights = np.array([1.0 / 3.0] + [1.0 / 6.0] * 4)
    r = noise_variance * np.eye(2)
    for t in range(steps):
        if t > 0:
            mean = mean @ transition.T
            covariance = np.einsum("ij,njk,lk->nil", transition, covariance, transition) + q
        root = np.linalg.cholesky(ensure_psd(covariance)) * math.sqrt(3.0)
        points = np.stack(
            [mean, mean + root[:, :, 0], mean - root[:, :, 0], mean + root[:, :, 1], mean - root[:, :, 1]],
            axis=1,
        )
        observed_points = observation(points, cubic)
        observed_mean = np.einsum("k,nkj->nj", weights, observed_points)
        dx = points - mean[:, None, :]
        dy = observed_points - observed_mean[:, None, :]
        cross = np.einsum("k,nki,nkj->nij", weights, dx, dy)
        observed_covariance = np.einsum("k,nki,nkj->nij", weights, dy, dy) + r
        gain = np.einsum("nij,njk->nik", cross, np.linalg.inv(observed_covariance))
        mean = mean + np.einsum("nij,nj->ni", gain, measured[:, t] - observed_mean)
        covariance = covariance - np.einsum(
            "nij,njk,nlk->nil", gain, observed_covariance, gain
        )
        covariance = ensure_psd(covariance)
        estimates[:, t], covariances[:, t] = mean, covariance
    return estimates, covariances


def systematic_indices(rng, weights):
    count = weights.shape[1]
    targets = (rng.random((len(weights), 1)) + np.arange(count)[None, :]) / count
    cdf = np.cumsum(weights, axis=1)
    result = np.empty_like(targets, dtype=int)
    for row in range(len(weights)):
        result[row] = np.searchsorted(cdf[row], targets[row], side="right")
    return np.minimum(result, count - 1)


def particle_sequence(rng, regime, measured, transition, process_scale, cubic, count=512):
    trajectories, steps, _ = measured.shape
    particles = standard_noise(rng, regime, (trajectories, count, 2))
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, 2, 2))
    for t in range(steps):
        if t > 0:
            particles = np.einsum("npd,ed->npe", particles, transition) + process_scale * standard_noise(
                rng, regime, particles.shape
            )
        likelihood = measurement_likelihood(
            measured[:, t, None, :] - observation(particles, cubic), regime
        )
        weights = likelihood / np.maximum(likelihood.sum(axis=1, keepdims=True), 1e-300)
        mean = np.einsum("np,npd->nd", weights, particles)
        centered = particles - mean[:, None, :]
        covariance = np.einsum("np,npi,npj->nij", weights, centered, centered)
        estimates[:, t], covariances[:, t] = mean, ensure_psd(covariance)
        indices = systematic_indices(rng, weights)
        particles = np.take_along_axis(particles, indices[:, :, None], axis=1)
    return estimates, covariances


def error_radius(error, covariance):
    inverse = np.linalg.inv(ensure_psd(covariance.reshape(-1, 2, 2))).reshape(covariance.shape)
    squared = np.einsum("...i,...ij,...j->...", error, inverse, error)
    return np.sqrt(np.maximum(squared, 0.0))


def metrics(estimate, covariance, state, tail_radius):
    error = estimate[:, 5:] - state[:, 5:]
    active_covariance = covariance[:, 5:]
    radius = error_radius(error, active_covariance)
    # RMS semi-axis of the reported 90% ellipse, in the original state units.
    # Coverage alone is not discriminating because a calibrated but enormous
    # ellipse can always cover the target.
    axis_radius90 = tail_radius * np.sqrt(
        np.trace(active_covariance, axis1=-2, axis2=-1) / 2.0
    )
    return {
        "rmse_vector": float(np.sqrt(np.mean(np.sum(error**2, axis=-1)))),
        "coverage90": float(np.mean(radius <= tail_radius)),
        "mean_error_radius": float(np.mean(radius)),
        "mean_axis_radius90": float(np.mean(axis_radius90)),
    }


def recursive_trial(closure, seed, regime, shifted):
    rng = np.random.default_rng(810000 + seed + 17 * REGIMES.index(regime) + int(shifted))
    transition = transition_matrix(shifted)
    cubic = 0.24 if shifted else 0.18
    state, measured = system_paths(rng, regime, 55, 58, transition, 0.30, cubic)
    started = time.perf_counter()
    compiled = compiled_sequence(closure, measured, transition, 0.30, cubic)
    compiled_time = time.perf_counter() - started
    ekf = ekf_sequence(measured, transition, 0.30, cubic, measurement_variance(regime))
    ukf = ukf_sequence(measured, transition, 0.30, cubic, measurement_variance(regime))
    started = time.perf_counter()
    particle = particle_sequence(
        np.random.default_rng(910000 + seed), regime, measured, transition, 0.30, cubic
    )
    particle_time = time.perf_counter() - started
    return {
        "seed": seed,
        "regime": regime,
        "shifted": shifted,
        "compiled": metrics(*compiled, state, closure.tail_radius90),
        "ekf": metrics(*ekf, state, math.sqrt(4.605170)),
        "ukf": metrics(*ukf, state, math.sqrt(4.605170)),
        "particle512": metrics(*particle, state, math.sqrt(4.605170)),
        "compiled_seconds": compiled_time,
        "particle_seconds": particle_time,
    }


def run_all():
    closures = {regime: compile_closure(regime) for regime in REGIMES}
    cases = [
        recursive_trial(closures[regime], seed, regime, shifted)
        for seed in range(10)
        for regime in REGIMES
        for shifted in (False, True)
    ]
    home = [c for c in cases if not c["shifted"]]
    mixture_home = [c for c in home if c["regime"] == "mixture"]
    shifted = [c for c in cases if c["shifted"]]
    mixture_shifted = [c for c in shifted if c["regime"] == "mixture"]
    summary = {
        "case_count": len(cases),
        "mixture_home_compiled_beats_ukf": sum(
            c["compiled"]["rmse_vector"] < c["ukf"]["rmse_vector"] for c in mixture_home
        ),
        "mixture_home_compiled_beats_ekf": sum(
            c["compiled"]["rmse_vector"] < c["ekf"]["rmse_vector"] for c in mixture_home
        ),
        "home_compiled_within_15pct_particle": sum(
            c["compiled"]["rmse_vector"] <= 1.15 * c["particle512"]["rmse_vector"]
            for c in home
        ),
        "mixture_shifted_compiled_beats_ukf": sum(
            c["compiled"]["rmse_vector"] < c["ukf"]["rmse_vector"]
            for c in mixture_shifted
        ),
        "mean_home_compiled_rmse": float(
            np.mean([c["compiled"]["rmse_vector"] for c in home])
        ),
        "mean_home_ukf_rmse": float(np.mean([c["ukf"]["rmse_vector"] for c in home])),
        "mean_home_particle_rmse": float(
            np.mean([c["particle512"]["rmse_vector"] for c in home])
        ),
        "mean_home_compiled_coverage90": float(
            np.mean([c["compiled"]["coverage90"] for c in home])
        ),
        "mean_home_compiled_axis_radius90": float(
            np.mean([c["compiled"]["mean_axis_radius90"] for c in home])
        ),
        "mean_home_ukf_axis_radius90": float(
            np.mean([c["ukf"]["mean_axis_radius90"] for c in home])
        ),
        "mean_home_particle_axis_radius90": float(
            np.mean([c["particle512"]["mean_axis_radius90"] for c in home])
        ),
        "compiled_tail_radius90": {
            regime: float(closure.tail_radius90) for regime, closure in closures.items()
        },
        "median_speedup_vs_particle512": float(
            np.median([c["particle_seconds"] / c["compiled_seconds"] for c in cases])
        ),
    }
    summary["status"] = (
        "WHITENED_MULTIVARIATE_RECURSIVE_CLOSURE_SURVIVES"
        if summary["mixture_home_compiled_beats_ukf"] >= 8
        and summary["mixture_shifted_compiled_beats_ukf"] >= 8
        and summary["home_compiled_within_15pct_particle"] >= 16
        and 0.87 <= summary["mean_home_compiled_coverage90"] <= 0.93
        and summary["mean_home_compiled_axis_radius90"]
        <= 1.20 * summary["mean_home_particle_axis_radius90"]
        else "MULTIVARIATE_CLOSURE_NOT_BROKEN"
    )
    return {"summary": summary, "cases": cases}


if __name__ == "__main__":
    started = time.perf_counter()
    result = run_all()
    result["elapsed_seconds"] = time.perf_counter() - started
    path = HERE / "R202_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"wrote {path}")
