from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
DIMENSIONS = (2, 4, 8)
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


def project_psd(matrix: np.ndarray, floor: float = 2e-4, ceiling: float = 12.0):
    symmetric = (matrix + np.swapaxes(matrix, -1, -2)) / 2.0
    values, vectors = np.linalg.eigh(symmetric)
    values = np.clip(values, floor, ceiling)
    return np.einsum("...ij,...j,...kj->...ik", vectors, values, vectors)


def ensure_psd(matrix: np.ndarray, floor: float = 1e-8):
    return project_psd(matrix, floor=floor, ceiling=100.0)


def observation(state: np.ndarray, cubic: float):
    following = np.roll(state, -1, axis=-1)
    previous = np.roll(state, 1, axis=-1)
    return state + cubic * state**3 + 0.10 * state * following - 0.07 * previous**2


def jacobian(state: np.ndarray, cubic: float):
    dimension = state.shape[-1]
    result = np.zeros(state.shape[:-1] + (dimension, dimension))
    following = np.roll(state, -1, axis=-1)
    previous = np.roll(state, 1, axis=-1)
    index = np.arange(dimension)
    result[..., index, index] = 1.0 + 3.0 * cubic * state**2 + 0.10 * following
    result[..., index, (index + 1) % dimension] += 0.10 * state
    result[..., index, (index - 1) % dimension] += -0.14 * previous
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


def measurement_log_likelihood(residual: np.ndarray, regime: str):
    def log_normal(value, sigma):
        return -0.5 * (value / sigma) ** 2 - math.log(math.sqrt(2.0 * math.pi) * sigma)

    if regime == "gaussian":
        component = log_normal(residual, 0.28)
    else:
        narrow = math.log(0.90) + log_normal(residual, 0.20)
        broad = math.log(0.10) + log_normal(residual, 1.25)
        component = np.logaddexp(narrow, broad)
    return np.sum(component, axis=-1)


def random_root(rng: np.random.Generator, count: int, dimension: int):
    diagonal = np.exp(
        rng.uniform(math.log(0.28), math.log(0.95), size=(count, dimension))
    )
    root = np.zeros((count, dimension, dimension))
    index = np.arange(dimension)
    root[:, index, index] = diagonal
    for row in range(1, dimension):
        root[:, row, row - 1] = (
            rng.uniform(-0.28, 0.28, count) * diagonal[:, row]
        )
        if row > 1:
            root[:, row, row - 2] = (
                rng.uniform(-0.08, 0.08, count) * diagonal[:, row]
            )
    return root


def sample_training_problem(
    rng: np.random.Generator,
    regime: str,
    count: int,
    dimension: int,
    cubic: float = 0.16,
):
    mean = rng.uniform(-1.15, 1.15, size=(count, dimension))
    root = random_root(rng, count, dimension)
    covariance = np.einsum("nij,nkj->nik", root, root)
    standardized = standard_noise(rng, regime, (count, dimension))
    state = mean + np.einsum("nij,nj->ni", root, standardized)
    measured = observation(state, cubic) + measurement_noise(rng, regime, state.shape)
    return mean, covariance, measured, state


def conditional_features(
    mean: np.ndarray,
    covariance: np.ndarray,
    measured: np.ndarray,
    cubic: float,
    noise_variance: float,
):
    count, dimension = mean.shape
    root = np.linalg.cholesky(ensure_psd(covariance))
    derivative = jacobian(mean, cubic)
    innovation_covariance = np.einsum(
        "nij,njk,nlk->nil", derivative, covariance, derivative
    ) + noise_variance * np.eye(dimension)[None, :, :]
    innovation_root = np.linalg.cholesky(ensure_psd(innovation_covariance))
    raw_innovation = measured - observation(mean, cubic)
    innovation = np.linalg.solve(innovation_root, raw_innovation[..., None])[..., 0]
    innovation = np.clip(innovation, -6.0, 6.0)
    linear_gain = np.einsum(
        "nij,nkj,nkl->nil",
        covariance,
        derivative,
        np.linalg.inv(innovation_covariance),
    )
    linear_state_correction = np.einsum(
        "nij,nj->ni", linear_gain, raw_innovation
    )
    identity = np.eye(dimension)[None, :, :]
    remainder = identity - np.einsum(
        "nij,njk->nik", linear_gain, derivative
    )
    # Joseph form preserves PSD under finite precision.  It is not the final
    # uncertainty claim: it is the coordinate chart in which the learned
    # conditional residual atoms live.
    linear_posterior_covariance = (
        np.einsum("nij,njk,nlk->nil", remainder, covariance, remainder)
        + noise_variance
        * np.einsum("nij,nkj->nik", linear_gain, linear_gain)
    )
    posterior_root = np.linalg.cholesky(ensure_psd(linear_posterior_covariance))

    log_scale = np.log(
        np.maximum(np.diagonal(root, axis1=-2, axis2=-1), 1e-8)
    )
    pair_row, pair_col = np.triu_indices(dimension)
    innovation_pairs = innovation[:, pair_row] * innovation[:, pair_col]
    features = np.concatenate(
        [
            np.ones((count, 1)),
            mean,
            log_scale,
            innovation,
            innovation_pairs,
            innovation**3,
            np.tanh(innovation),
            mean * innovation,
            log_scale * innovation,
            derivative.reshape(count, dimension * dimension),
        ],
        axis=1,
    )
    return features, posterior_root, innovation, linear_state_correction


def discover_voronoi_language(
    innovation: np.ndarray,
    atom_count: int,
    rng: np.random.Generator,
    sample_limit: int = 12_000,
    iterations: int = 8,
):
    if len(innovation) > sample_limit:
        selected = rng.choice(len(innovation), size=sample_limit, replace=False)
        sample = innovation[selected]
    else:
        sample = innovation.copy()

    centers = np.empty((atom_count, innovation.shape[1]))
    centers[0] = sample[rng.integers(len(sample))]
    nearest = np.sum((sample - centers[0]) ** 2, axis=1)
    for index in range(1, atom_count):
        total = float(np.sum(nearest))
        if total <= 1e-15:
            centers[index] = sample[index % len(sample)]
        else:
            centers[index] = sample[rng.choice(len(sample), p=nearest / total)]
        nearest = np.minimum(nearest, np.sum((sample - centers[index]) ** 2, axis=1))

    for _ in range(iterations):
        distance = np.sum((sample[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        assignment = np.argmin(distance, axis=1)
        closest = np.min(distance, axis=1)
        for index in range(atom_count):
            member = sample[assignment == index]
            if len(member):
                centers[index] = member.mean(axis=0)
            else:
                centers[index] = sample[int(np.argmax(closest))]

    all_distance = np.sum(
        (innovation[:, None, :] - centers[None, :, :]) ** 2, axis=2
    )
    assignment = np.argmin(all_distance, axis=1)
    radius = np.empty(atom_count)
    fallback = float(np.median(np.min(all_distance, axis=1))) + 1e-3
    for index in range(atom_count):
        member_distance = all_distance[assignment == index, index]
        radius[index] = float(np.mean(member_distance)) if len(member_distance) else fallback
    return centers, np.maximum(radius, 0.08), assignment


@dataclass
class AutomaticPSDClosure:
    dimension: int
    center: np.ndarray
    spread: np.ndarray
    mean_coefficient: np.ndarray
    innovation_centers: np.ndarray
    innovation_radius: np.ndarray
    covariance_atoms: np.ndarray
    tail_radius90: float
    noise_variance: float

    def update(self, prior_mean, prior_covariance, measured, cubic: float):
        features, posterior_root, innovation, linear_state_correction = conditional_features(
            prior_mean, prior_covariance, measured, cubic, self.noise_variance
        )
        normalized = np.clip((features - self.center) / self.spread, -8.0, 8.0)
        # The analytic linear posterior is a PSD coordinate chart.  Learned
        # terms can bend it, but never erase the safe baseline update.
        correction = normalized @ self.mean_coefficient
        distance = np.sum(
            (innovation[:, None, :] - self.innovation_centers[None, :, :]) ** 2,
            axis=2,
        ) / self.innovation_radius[None, :]
        log_weight = -0.5 * distance
        log_weight -= np.max(log_weight, axis=1, keepdims=True)
        weight = np.exp(log_weight)
        weight /= np.maximum(np.sum(weight, axis=1, keepdims=True), 1e-300)
        normalized_covariance = np.einsum(
            "nk,kij->nij", weight, self.covariance_atoms
        )
        posterior_mean = (
            prior_mean
            + linear_state_correction
            + np.einsum("nij,nj->ni", posterior_root, correction)
        )
        posterior_covariance = np.einsum(
            "nij,njk,nlk->nil",
            posterior_root,
            normalized_covariance,
            posterior_root,
        )
        return posterior_mean, posterior_covariance

    @property
    def model_bytes(self):
        arrays = (
            self.center,
            self.spread,
            self.mean_coefficient,
            self.innovation_centers,
            self.innovation_radius,
            self.covariance_atoms,
        )
        return int(sum(value.nbytes for value in arrays))


def chi_radius90(dimension: int):
    # Wilson-Hilferty approximation to sqrt(chi-square_0.90(d)); exact enough
    # for baseline reporting, while the compiled closure is calibrated directly.
    z90 = 1.2815515655446004
    quantile = dimension * (
        1.0 - 2.0 / (9.0 * dimension) + z90 * math.sqrt(2.0 / (9.0 * dimension))
    ) ** 3
    return math.sqrt(quantile)


def compile_closure(
    dimension: int,
    regime: str,
    seed: int = 0,
    training_count: int | None = None,
    calibration_trajectories: int = 120,
):
    started = time.perf_counter()
    if training_count is None:
        training_count = {2: 60_000, 4: 42_000, 8: 30_000}.get(
            dimension, max(10_000, 36_000 // max(1, dimension // 4))
        )
    rng = np.random.default_rng(
        1_203_000 + 101 * dimension + 17 * REGIMES.index(regime) + seed
    )
    mean, covariance, measured, state = sample_training_problem(
        rng, regime, training_count, dimension
    )
    features, posterior_root, innovation, linear_state_correction = conditional_features(
        mean, covariance, measured, 0.16, measurement_variance(regime)
    )
    center = features.mean(axis=0)
    spread = np.maximum(features.std(axis=0), 1e-8)
    center[0], spread[0] = 0.0, 1.0
    normalized = (features - center) / spread
    linear_posterior_mean = mean + linear_state_correction
    standardized = np.linalg.solve(
        posterior_root, (state - linear_posterior_mean)[..., None]
    )[..., 0]
    mean_coefficient = ridge(normalized, standardized, 4e-5)
    first_residual = standardized - normalized @ mean_coefficient
    robust_scale = np.median(np.linalg.norm(first_residual, axis=1)) / max(
        math.sqrt(dimension), 1.0
    )
    robust_weight = 1.0 / (
        1.0
        + (
            np.linalg.norm(first_residual, axis=1)
            / max(2.8 * robust_scale * math.sqrt(dimension), 1e-6)
        )
        ** 2
    )
    mean_coefficient = ridge(normalized, standardized, 4e-5, robust_weight)
    residual = standardized - normalized @ mean_coefficient

    atom_count = 4 + 2 * dimension
    centers, radius, assignment = discover_voronoi_language(
        innovation, atom_count, rng
    )
    global_covariance = project_psd(
        ((residual.T @ residual) / len(residual))[None]
    )[0]
    covariance_atoms = np.empty((atom_count, dimension, dimension))
    shrinkage = 100.0 + 10.0 * dimension
    for index in range(atom_count):
        selected = residual[assignment == index]
        scatter = (
            selected.T @ selected
            if len(selected)
            else np.zeros((dimension, dimension))
        )
        covariance_atoms[index] = (
            scatter + shrinkage * global_covariance
        ) / (len(selected) + shrinkage)
    covariance_atoms = project_psd(covariance_atoms)
    closure = AutomaticPSDClosure(
        dimension,
        center,
        spread,
        mean_coefficient,
        centers,
        radius,
        covariance_atoms,
        chi_radius90(dimension),
        measurement_variance(regime),
    )

    if calibration_trajectories:
        calibration_rng = np.random.default_rng(
            1_303_000 + 101 * dimension + 17 * REGIMES.index(regime) + seed
        )
        state_path, measured_path = system_paths(
            calibration_rng,
            regime,
            calibration_trajectories,
            48,
            transition_matrix(dimension, False),
            0.28,
            0.16,
        )
        estimate, posterior_covariance = compiled_sequence(
            closure,
            measured_path,
            transition_matrix(dimension, False),
            0.28,
            0.16,
        )
        radius_sample = error_radius(
            estimate[:, 5:] - state_path[:, 5:], posterior_covariance[:, 5:]
        )
        closure.tail_radius90 = float(np.quantile(radius_sample, 0.90))

    atom_bytes = int(covariance_atoms.nbytes)
    cartesian_atoms = 10**dimension
    compile_info = {
        "dimension": dimension,
        "regime": regime,
        "training_count": training_count,
        "feature_count": int(features.shape[1]),
        "atom_count": atom_count,
        "atom_storage_bytes": atom_bytes,
        "model_storage_bytes": closure.model_bytes,
        "cartesian_10bin_atom_count": cartesian_atoms,
        "cartesian_10bin_covariance_bytes": int(
            cartesian_atoms * dimension * dimension * 8
        ),
        "atom_storage_reduction": float(
            cartesian_atoms * dimension * dimension * 8 / atom_bytes
        ),
        "minimum_atom_eigenvalue": float(
            np.min(np.linalg.eigvalsh(covariance_atoms))
        ),
        "tail_radius90": closure.tail_radius90,
        "compile_seconds": time.perf_counter() - started,
    }
    return closure, compile_info


def transition_matrix(dimension: int, shifted: bool):
    diagonal = 0.89 if shifted else 0.82
    previous = 0.11 if shifted else 0.08
    following = -0.05 if shifted else -0.03
    matrix = diagonal * np.eye(dimension)
    index = np.arange(dimension)
    matrix[index, (index - 1) % dimension] += previous
    matrix[index, (index + 1) % dimension] += following
    return matrix


def system_paths(
    rng,
    regime,
    trajectories,
    steps,
    transition,
    process_scale,
    cubic,
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
    measured = observation(state, cubic) + measurement_noise(
        rng, regime, state.shape
    )
    return state, measured


def compiled_sequence(closure, measured, transition, process_scale, cubic):
    trajectories, steps, dimension = measured.shape
    mean = np.zeros((trajectories, dimension))
    covariance = np.repeat(np.eye(dimension)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, dimension, dimension))
    process_covariance = process_scale**2 * np.eye(dimension)
    for step in range(steps):
        if step:
            mean = mean @ transition.T
            covariance = np.einsum(
                "ij,njk,lk->nil", transition, covariance, transition
            ) + process_covariance
        mean, covariance = closure.update(mean, covariance, measured[:, step], cubic)
        estimates[:, step], covariances[:, step] = mean, covariance
    return estimates, covariances


def ekf_sequence(measured, transition, process_scale, cubic, noise_variance):
    trajectories, steps, dimension = measured.shape
    mean = np.zeros((trajectories, dimension))
    covariance = np.repeat(np.eye(dimension)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, dimension, dimension))
    process_covariance = process_scale**2 * np.eye(dimension)
    measurement_covariance = noise_variance * np.eye(dimension)
    identity = np.eye(dimension)[None, :, :]
    for step in range(steps):
        if step:
            mean = mean @ transition.T
            covariance = np.einsum(
                "ij,njk,lk->nil", transition, covariance, transition
            ) + process_covariance
        derivative = jacobian(mean, cubic)
        innovation_covariance = np.einsum(
            "nij,njk,nlk->nil", derivative, covariance, derivative
        ) + measurement_covariance
        gain = np.einsum(
            "nij,nkj,nkl->nil",
            covariance,
            derivative,
            np.linalg.inv(innovation_covariance),
        )
        mean = mean + np.einsum(
            "nij,nj->ni", gain, measured[:, step] - observation(mean, cubic)
        )
        covariance = np.einsum(
            "nij,njk->nik",
            identity - np.einsum("nij,njk->nik", gain, derivative),
            covariance,
        )
        covariance = ensure_psd(covariance)
        estimates[:, step], covariances[:, step] = mean, covariance
    return estimates, covariances


def ukf_sequence(measured, transition, process_scale, cubic, noise_variance):
    trajectories, steps, dimension = measured.shape
    mean = np.zeros((trajectories, dimension))
    covariance = np.repeat(np.eye(dimension)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, dimension, dimension))
    process_covariance = process_scale**2 * np.eye(dimension)
    measurement_covariance = noise_variance * np.eye(dimension)
    scale = math.sqrt(dimension + 1.0)
    weights = np.array(
        [1.0 / (dimension + 1.0)]
        + [1.0 / (2.0 * (dimension + 1.0))] * (2 * dimension)
    )
    for step in range(steps):
        if step:
            mean = mean @ transition.T
            covariance = np.einsum(
                "ij,njk,lk->nil", transition, covariance, transition
            ) + process_covariance
        root = np.linalg.cholesky(ensure_psd(covariance)) * scale
        offset = np.transpose(root, (0, 2, 1))
        points = np.concatenate(
            [mean[:, None, :], mean[:, None, :] + offset, mean[:, None, :] - offset],
            axis=1,
        )
        observed_points = observation(points, cubic)
        observed_mean = np.einsum("k,nkj->nj", weights, observed_points)
        dx = points - mean[:, None, :]
        dy = observed_points - observed_mean[:, None, :]
        cross = np.einsum("k,nki,nkj->nij", weights, dx, dy)
        observed_covariance = (
            np.einsum("k,nki,nkj->nij", weights, dy, dy)
            + measurement_covariance
        )
        gain = np.einsum(
            "nij,njk->nik", cross, np.linalg.inv(observed_covariance)
        )
        mean = mean + np.einsum(
            "nij,nj->ni", gain, measured[:, step] - observed_mean
        )
        covariance = covariance - np.einsum(
            "nij,njk,nlk->nil", gain, observed_covariance, gain
        )
        covariance = ensure_psd(covariance)
        estimates[:, step], covariances[:, step] = mean, covariance
    return estimates, covariances


def systematic_indices(rng, weights):
    count = weights.shape[1]
    targets = (rng.random((len(weights), 1)) + np.arange(count)[None, :]) / count
    cdf = np.cumsum(weights, axis=1)
    result = np.empty_like(targets, dtype=int)
    for row in range(len(weights)):
        result[row] = np.searchsorted(cdf[row], targets[row], side="right")
    return np.minimum(result, count - 1)


def particle_sequence(
    rng,
    regime,
    measured,
    transition,
    process_scale,
    cubic,
    count=384,
):
    trajectories, steps, dimension = measured.shape
    particles = standard_noise(rng, regime, (trajectories, count, dimension))
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, dimension, dimension))
    for step in range(steps):
        if step:
            particles = (
                np.einsum("npd,ed->npe", particles, transition)
                + process_scale * standard_noise(rng, regime, particles.shape)
            )
        log_weight = measurement_log_likelihood(
            measured[:, step, None, :] - observation(particles, cubic), regime
        )
        log_weight -= np.max(log_weight, axis=1, keepdims=True)
        weights = np.exp(log_weight)
        weights /= np.maximum(np.sum(weights, axis=1, keepdims=True), 1e-300)
        mean = np.einsum("np,npd->nd", weights, particles)
        centered = particles - mean[:, None, :]
        covariance = np.einsum("np,npi,npj->nij", weights, centered, centered)
        estimates[:, step], covariances[:, step] = mean, ensure_psd(covariance)
        indices = systematic_indices(rng, weights)
        particles = np.take_along_axis(particles, indices[:, :, None], axis=1)
    return estimates, covariances


def error_radius(error, covariance):
    dimension = error.shape[-1]
    inverse = np.linalg.inv(
        ensure_psd(covariance.reshape(-1, dimension, dimension))
    ).reshape(covariance.shape)
    squared = np.einsum("...i,...ij,...j->...", error, inverse, error)
    return np.sqrt(np.maximum(squared, 0.0))


def metrics(estimate, covariance, state, tail_radius):
    dimension = state.shape[-1]
    error = estimate[:, 5:] - state[:, 5:]
    active_covariance = covariance[:, 5:]
    radius = error_radius(error, active_covariance)
    axis_radius90 = tail_radius * np.sqrt(
        np.trace(active_covariance, axis1=-2, axis2=-1) / dimension
    )
    return {
        "rmse_vector": float(np.sqrt(np.mean(np.sum(error**2, axis=-1)))),
        "rmse_per_coordinate": float(np.sqrt(np.mean(error**2))),
        "coverage90": float(np.mean(radius <= tail_radius)),
        "mean_error_radius": float(np.mean(radius)),
        "mean_axis_radius90": float(np.mean(axis_radius90)),
        "minimum_covariance_eigenvalue": float(
            np.min(
                np.linalg.eigvalsh(
                    active_covariance.reshape(-1, dimension, dimension)
                )
            )
        ),
    }


def recursive_trial(closure, seed, regime, shifted):
    dimension = closure.dimension
    rng = np.random.default_rng(
        1_403_000
        + 1009 * dimension
        + 31 * seed
        + 17 * REGIMES.index(regime)
        + int(shifted)
    )
    transition = transition_matrix(dimension, shifted)
    cubic = 0.22 if shifted else 0.16
    state, measured = system_paths(
        rng, regime, 28, 50, transition, 0.28, cubic
    )
    started = time.perf_counter()
    compiled = compiled_sequence(closure, measured, transition, 0.28, cubic)
    compiled_seconds = time.perf_counter() - started
    ekf = ekf_sequence(
        measured, transition, 0.28, cubic, measurement_variance(regime)
    )
    ukf = ukf_sequence(
        measured, transition, 0.28, cubic, measurement_variance(regime)
    )
    started = time.perf_counter()
    particle = particle_sequence(
        np.random.default_rng(1_503_000 + 1009 * dimension + 31 * seed),
        regime,
        measured,
        transition,
        0.28,
        cubic,
    )
    particle_seconds = time.perf_counter() - started
    baseline_radius = chi_radius90(dimension)
    return {
        "dimension": dimension,
        "seed": seed,
        "regime": regime,
        "shifted": shifted,
        "compiled": metrics(*compiled, state, closure.tail_radius90),
        "ekf": metrics(*ekf, state, baseline_radius),
        "ukf": metrics(*ukf, state, baseline_radius),
        "particle384": metrics(*particle, state, baseline_radius),
        "compiled_seconds": compiled_seconds,
        "particle_seconds": particle_seconds,
    }


def mean_metric(cases, method, metric):
    return float(np.mean([case[method][metric] for case in cases]))


def run_all():
    closures = {}
    compile_records = []
    for dimension in DIMENSIONS:
        for regime in REGIMES:
            closure, record = compile_closure(dimension, regime)
            closures[(dimension, regime)] = closure
            compile_records.append(record)

    cases = [
        recursive_trial(closures[(dimension, regime)], seed, regime, shifted)
        for dimension in DIMENSIONS
        for seed in range(3)
        for regime in REGIMES
        for shifted in (False, True)
    ]
    dimension_summary = {}
    for dimension in DIMENSIONS:
        selected = [case for case in cases if case["dimension"] == dimension]
        home = [case for case in selected if not case["shifted"]]
        mixture = [case for case in selected if case["regime"] == "mixture"]
        compile_for_dimension = [
            record for record in compile_records if record["dimension"] == dimension
        ]
        dimension_summary[str(dimension)] = {
            "case_count": len(selected),
            "home_compiled_rmse_per_coordinate": mean_metric(
                home, "compiled", "rmse_per_coordinate"
            ),
            "home_ukf_rmse_per_coordinate": mean_metric(
                home, "ukf", "rmse_per_coordinate"
            ),
            "home_particle_rmse_per_coordinate": mean_metric(
                home, "particle384", "rmse_per_coordinate"
            ),
            "home_compiled_coverage90": mean_metric(
                home, "compiled", "coverage90"
            ),
            "home_compiled_axis_radius90": mean_metric(
                home, "compiled", "mean_axis_radius90"
            ),
            "home_particle_axis_radius90": mean_metric(
                home, "particle384", "mean_axis_radius90"
            ),
            "mixture_compiled_beats_ukf": int(
                sum(
                    case["compiled"]["rmse_per_coordinate"]
                    < case["ukf"]["rmse_per_coordinate"]
                    for case in mixture
                )
            ),
            "mixture_case_count": len(mixture),
            "home_within_20pct_particle": int(
                sum(
                    case["compiled"]["rmse_per_coordinate"]
                    <= 1.20 * case["particle384"]["rmse_per_coordinate"]
                    for case in home
                )
            ),
            "home_case_count": len(home),
            "median_speedup_vs_particle384": float(
                np.median(
                    [
                        case["particle_seconds"] / case["compiled_seconds"]
                        for case in selected
                    ]
                )
            ),
            "maximum_model_storage_bytes": max(
                record["model_storage_bytes"] for record in compile_for_dimension
            ),
            "maximum_atom_count": max(
                record["atom_count"] for record in compile_for_dimension
            ),
            "minimum_atom_storage_reduction": min(
                record["atom_storage_reduction"]
                for record in compile_for_dimension
            ),
            "minimum_deployed_covariance_eigenvalue": min(
                case["compiled"]["minimum_covariance_eigenvalue"]
                for case in selected
            ),
        }

    coverage_ok = all(
        0.84 <= row["home_compiled_coverage90"] <= 0.96
        for row in dimension_summary.values()
    )
    sharpness_ok = all(
        row["home_compiled_axis_radius90"]
        <= 1.50 * row["home_particle_axis_radius90"]
        for row in dimension_summary.values()
    )
    psd_ok = all(
        row["minimum_deployed_covariance_eigenvalue"] > 0.0
        for row in dimension_summary.values()
    )
    approximation_ok = sum(
        row["home_within_20pct_particle"] for row in dimension_summary.values()
    ) >= 14
    scaling_ok = (
        dimension_summary["8"]["maximum_atom_count"] <= 20
        and dimension_summary["8"]["minimum_atom_storage_reduction"] >= 1_000_000
    )
    summary = {
        "case_count": len(cases),
        "dimensions": list(DIMENSIONS),
        "automatic_language": "whitened-innovation Voronoi prototypes with soft convex PSD atom mixing",
        "coverage_gate": coverage_ok,
        "sharpness_gate": sharpness_ok,
        "psd_gate": psd_ok,
        "particle_approximation_gate": approximation_ok,
        "scaling_gate": scaling_ok,
        "dimension_summary": dimension_summary,
    }
    summary["status"] = (
        "AUTOMATIC_PSD_ATOM_LANGUAGE_SURVIVES_FIRST_PASS"
        if coverage_ok and sharpness_ok and psd_ok and approximation_ok and scaling_ok
        else "AUTOMATIC_PSD_ATOM_LANGUAGE_NEEDS_MUTATION"
    )
    return {"summary": summary, "compile_records": compile_records, "cases": cases}


if __name__ == "__main__":
    started = time.perf_counter()
    result = run_all()
    result["elapsed_seconds"] = time.perf_counter() - started
    path = HERE / "R203_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"elapsed_seconds={result['elapsed_seconds']:.3f}")
    print(f"wrote {path}")
