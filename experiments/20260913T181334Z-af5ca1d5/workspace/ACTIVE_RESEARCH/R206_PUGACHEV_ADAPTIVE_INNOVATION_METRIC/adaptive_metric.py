from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
R203 = HERE.parent / "R203_PUGACHEV_AUTOMATIC_PSD_ATOM_LANGUAGE"
sys.path.insert(0, str(R203))

from automatic_psd_closure import (  # noqa: E402
    AutomaticPSDClosure,
    ensure_psd,
    jacobian,
    measurement_noise,
    observation,
    standard_noise,
)


def compound_correlation(dimension: int, rho: float) -> np.ndarray:
    """A unit-diagonal equicorrelation matrix with an exact PSD bound."""
    lower = -1.0 / max(dimension - 1, 1)
    if not lower <= rho <= 1.0:
        raise ValueError(f"rho={rho} is outside [{lower}, 1]")
    return (1.0 - rho) * np.eye(dimension) + rho * np.ones(
        (dimension, dimension)
    )


def signed_rank_one_correlation(dimension: int, strength: float) -> np.ndarray:
    """A PSD correlation whose positive and negative off-diagonals cancel."""
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must lie in [0, 1]")
    sign = np.ones(dimension)
    sign[1::2] = -1.0
    return (1.0 - strength) * np.eye(dimension) + strength * np.outer(sign, sign)


def correlation_retraction(matrix: np.ndarray, shrinkage: float) -> np.ndarray:
    """Map arbitrary symmetric matrices to positive definite correlations.

    This is a single spectral pass followed by diagonal normalization.  It is
    deliberately not advertised as the nearest-correlation projection.
    """
    symmetric = (matrix + np.swapaxes(matrix, -1, -2)) / 2.0
    values, vectors = np.linalg.eigh(symmetric)
    values = np.clip(values, 1e-4, None)
    positive = np.einsum("...ij,...j,...kj->...ik", vectors, values, vectors)
    diagonal = np.sqrt(
        np.maximum(np.diagonal(positive, axis1=-2, axis2=-1), 1e-12)
    )
    correlation = positive / (diagonal[..., :, None] * diagonal[..., None, :])
    dimension = correlation.shape[-1]
    identity = np.eye(dimension)
    return (1.0 - shrinkage) * identity + shrinkage * correlation


def conditional_features_with_metric(
    mean: np.ndarray,
    covariance: np.ndarray,
    measured: np.ndarray,
    cubic: float,
    measurement_covariance: np.ndarray,
    bounded_ray: bool = True,
):
    """R203 feature chart with a general positive definite measurement metric."""
    count, dimension = mean.shape
    if measurement_covariance.ndim == 2:
        measurement_covariance = np.broadcast_to(
            measurement_covariance, (count, dimension, dimension)
        )
    root = np.linalg.cholesky(ensure_psd(covariance))
    derivative = jacobian(mean, cubic)
    state_innovation_covariance = np.einsum(
        "nij,njk,nlk->nil", derivative, covariance, derivative
    )
    innovation_covariance = state_innovation_covariance + measurement_covariance
    innovation_covariance = ensure_psd(innovation_covariance)
    innovation_root = np.linalg.cholesky(innovation_covariance)
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
    if bounded_ray:
        # A full EKF step can catastrophically overshoot a strongly nonlinear
        # observation even when R is known.  Select from a fixed ray that
        # includes the zero step, using the nonlinear local posterior objective.
        displacement_cost = np.einsum(
            "ni,nij,nj->n",
            linear_state_correction,
            np.linalg.inv(ensure_psd(covariance)),
            linear_state_correction,
        )
        risky_step = (
            displacement_cost > 6.25 * dimension
        ) | (np.sum(innovation**2, axis=1) > 9.0 * dimension)
        step_fraction = np.ones(count)
        if np.any(risky_step):
            fractions = np.array([0.0, 0.0625, 0.125, 0.25, 0.5, 0.75, 1.0])
            active_mean = mean[risky_step]
            active_correction = linear_state_correction[risky_step]
            candidate = (
                active_mean[:, None, :]
                + fractions[None, :, None]
                * active_correction[:, None, :]
            )
            candidate_residual = (
                measured[risky_step, None, :] - observation(candidate, cubic)
            )
            inverse_measurement = np.linalg.inv(
                measurement_covariance[risky_step]
            )
            measurement_cost = np.einsum(
                "nai,nij,naj->na",
                candidate_residual,
                inverse_measurement,
                candidate_residual,
            )
            objective = (
                fractions[None, :] ** 2
                * displacement_cost[risky_step, None]
                + measurement_cost
            )
            step_fraction[risky_step] = fractions[
                np.argmin(objective, axis=1)
            ]
        linear_gain = linear_gain * step_fraction[:, None, None]
        linear_state_correction = (
            linear_state_correction * step_fraction[:, None]
        )
    else:
        step_fraction = np.ones(count)
        risky_step = np.zeros(count, dtype=bool)
    identity = np.eye(dimension)[None, :, :]
    remainder = identity - np.einsum(
        "nij,njk->nik", linear_gain, derivative
    )
    linear_posterior_covariance = (
        np.einsum("nij,njk,nlk->nil", remainder, covariance, remainder)
        + np.einsum(
            "nij,njk,nlk->nil",
            linear_gain,
            measurement_covariance,
            linear_gain,
        )
    )
    posterior_root = np.linalg.cholesky(
        ensure_psd(linear_posterior_covariance)
    )

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
    return (
        features,
        posterior_root,
        innovation,
        linear_state_correction,
        raw_innovation,
        state_innovation_covariance,
        step_fraction,
        risky_step,
    )


def update_with_metric(
    closure: AutomaticPSDClosure,
    prior_mean: np.ndarray,
    prior_covariance: np.ndarray,
    measured: np.ndarray,
    cubic: float,
    measurement_covariance: np.ndarray,
    support_gate: bool = True,
):
    (
        features,
        posterior_root,
        innovation,
        linear_state_correction,
        raw_innovation,
        state_innovation_covariance,
        step_fraction,
        risky_step,
    ) = conditional_features_with_metric(
        prior_mean,
        prior_covariance,
        measured,
        cubic,
        measurement_covariance,
        bounded_ray=support_gate,
    )
    raw_normalized = (features - closure.center) / closure.spread
    normalized = np.clip(raw_normalized, -8.0, 8.0)
    correction = normalized @ closure.mean_coefficient
    distance = np.sum(
        (
            innovation[:, None, :]
            - closure.innovation_centers[None, :, :]
        )
        ** 2,
        axis=2,
    ) / closure.innovation_radius[None, :]
    log_weight = -0.5 * distance
    log_weight -= np.max(log_weight, axis=1, keepdims=True)
    weight = np.exp(log_weight)
    weight /= np.maximum(np.sum(weight, axis=1, keepdims=True), 1e-300)
    if support_gate:
        # Input clipping alone can map many far-out feature vectors to the same
        # artificial boundary point.  Fade learned corrections continuously as
        # either the compiled feature chart or innovation dictionary is left.
        feature_excess = np.maximum(
            np.max(np.abs(raw_normalized), axis=1) - 6.5, 0.0
        )
        innovation_distance = np.sqrt(np.maximum(np.min(distance, axis=1), 0.0))
        innovation_excess = np.maximum(innovation_distance - 3.5, 0.0)
        reliability = np.exp(
            -0.5 * (feature_excess / 2.0) ** 2
            -0.5 * innovation_excess**2
        )
        reliability = np.where(risky_step, reliability, 1.0)
        correction_norm = np.linalg.norm(correction, axis=1)
        correction_cap = 2.5 * math.sqrt(closure.dimension)
        correction_scale = np.minimum(
            1.0, correction_cap / np.maximum(correction_norm, 1e-12)
        )
        correction *= (reliability * correction_scale)[:, None]
    else:
        reliability = np.ones(len(prior_mean))
    normalized_covariance = np.einsum(
        "nk,kij->nij", weight, closure.covariance_atoms
    )
    if support_gate:
        identity_atom = np.eye(closure.dimension)[None, :, :]
        normalized_covariance = (
            reliability[:, None, None] * normalized_covariance
            + (1.0 - reliability[:, None, None]) * identity_atom
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
    return (
        posterior_mean,
        posterior_covariance,
        raw_innovation,
        state_innovation_covariance,
        reliability,
        step_fraction,
        risky_step,
    )


@dataclass(frozen=True)
class AdaptationConfig:
    family: str
    gain: float = 0.08
    shrinkage: float = 0.72
    moment_clip: float = 4.0
    shared_across_batch: bool = False
    activation_threshold: float = 0.0


def _measurement_covariance(
    raw_moment: np.ndarray,
    variance: float,
    config: AdaptationConfig,
) -> tuple[np.ndarray, np.ndarray]:
    dimension = raw_moment.shape[-1]
    if config.family == "compound":
        mask = ~np.eye(dimension, dtype=bool)
        rho = np.mean(raw_moment[..., mask], axis=-1)
        rho = np.where(np.abs(rho) >= config.activation_threshold, rho, 0.0)
        lower = -1.0 / max(dimension - 1, 1) + 1e-4
        rho = np.clip(config.shrinkage * rho, lower, 0.999)
        if np.ndim(rho) == 0:
            correlation = compound_correlation(dimension, float(rho))
        else:
            identity = np.eye(dimension)
            ones = np.ones((dimension, dimension))
            correlation = (
                (1.0 - rho[..., None, None]) * identity
                + rho[..., None, None] * ones
            )
    elif config.family == "full":
        unshrunk = correlation_retraction(raw_moment, 1.0)
        mask = ~np.eye(dimension, dtype=bool)
        signal = np.sqrt(np.mean(raw_moment[..., mask] ** 2, axis=-1))
        active = signal >= config.activation_threshold
        effective = config.shrinkage * active
        correlation = (
            np.eye(dimension)
            + effective[..., None, None]
            * (unshrunk - np.eye(dimension))
        )
    else:
        raise ValueError(config.family)
    return variance * correlation, correlation


def adaptive_compiled_sequence(
    closure: AutomaticPSDClosure,
    measured: np.ndarray,
    transition: np.ndarray,
    process_scale: float,
    cubic: float,
    config: AdaptationConfig,
):
    trajectories, steps, dimension = measured.shape
    mean = np.zeros((trajectories, dimension))
    covariance = np.repeat(np.eye(dimension)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, dimension, dimension))
    correlations = np.zeros((trajectories, steps, dimension, dimension))
    reliability_trace = np.ones((trajectories, steps))
    fraction_trace = np.ones((trajectories, steps))
    process_covariance = process_scale**2 * np.eye(dimension)
    if config.shared_across_batch:
        raw_moment = np.eye(dimension)
    else:
        raw_moment = np.repeat(
            np.eye(dimension)[None, :, :], trajectories, axis=0
        )

    for step in range(steps):
        if step:
            mean = mean @ transition.T
            covariance = np.einsum(
                "ij,njk,lk->nil", transition, covariance, transition
            ) + process_covariance

        measurement_covariance, correlation = _measurement_covariance(
            raw_moment, closure.noise_variance, config
        )
        if measurement_covariance.ndim == 2:
            deployed_covariance = np.broadcast_to(
                measurement_covariance,
                (trajectories, dimension, dimension),
            )
            deployed_correlation = np.broadcast_to(
                correlation, (trajectories, dimension, dimension)
            )
        else:
            deployed_covariance = measurement_covariance
            deployed_correlation = correlation

        (
            mean,
            covariance,
            raw_innovation,
            state_innovation_covariance,
            reliability,
            step_fraction,
            risky_step,
        ) = update_with_metric(
            closure,
            mean,
            covariance,
            measured[:, step],
            cubic,
            deployed_covariance,
        )
        estimates[:, step], covariances[:, step] = mean, covariance
        correlations[:, step] = deployed_correlation
        reliability_trace[:, step] = reliability
        fraction_trace[:, step] = step_fraction

        # E[nu nu^T - HPH] = R when the prior first two moments are correct.
        # The current observation only affects the next update, so the metric
        # remains predictable rather than fitting its own residual.
        outer = np.einsum("ni,nj->nij", raw_innovation, raw_innovation)
        candidate = (
            outer - state_innovation_covariance
        ) / closure.noise_variance
        candidate = np.clip(
            candidate, -config.moment_clip, config.moment_clip
        )
        index = np.arange(dimension)
        candidate[:, index, index] = 1.0
        if config.shared_across_batch:
            candidate_update = np.mean(candidate, axis=0)
        else:
            candidate_update = candidate
        raw_moment = (
            (1.0 - config.gain) * raw_moment
            + config.gain * candidate_update
        )

    off_diagonal = correlations - np.eye(dimension)[None, None, :, :]
    diagnostics = {
        "mean_reliability": float(np.mean(reliability_trace)),
        "fraction_support_faded": float(np.mean(reliability_trace < 0.999)),
        "fraction_bounded_ray": float(np.mean(fraction_trace < 0.999)),
        "fraction_metric_active": float(
            np.mean(np.max(np.abs(off_diagonal), axis=(-1, -2)) > 1e-10)
        ),
    }
    return estimates, covariances, correlations, diagnostics


def fixed_metric_sequence(
    closure: AutomaticPSDClosure,
    measured: np.ndarray,
    transition: np.ndarray,
    process_scale: float,
    cubic: float,
    measurement_covariance: np.ndarray,
    support_gate: bool = True,
    return_diagnostics: bool = False,
):
    trajectories, steps, dimension = measured.shape
    mean = np.zeros((trajectories, dimension))
    covariance = np.repeat(np.eye(dimension)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, dimension, dimension))
    reliability_trace = np.ones((trajectories, steps))
    fraction_trace = np.ones((trajectories, steps))
    process_covariance = process_scale**2 * np.eye(dimension)
    deployed = np.broadcast_to(
        measurement_covariance, (trajectories, dimension, dimension)
    )
    for step in range(steps):
        if step:
            mean = mean @ transition.T
            covariance = np.einsum(
                "ij,njk,lk->nil", transition, covariance, transition
            ) + process_covariance
        mean, covariance, _, _, reliability, fraction, _ = update_with_metric(
            closure,
            mean,
            covariance,
            measured[:, step],
            cubic,
            deployed,
            support_gate=support_gate,
        )
        estimates[:, step], covariances[:, step] = mean, covariance
        reliability_trace[:, step] = reliability
        fraction_trace[:, step] = fraction
    if return_diagnostics:
        return estimates, covariances, {
            "mean_reliability": float(np.mean(reliability_trace)),
            "fraction_support_faded": float(np.mean(reliability_trace < 0.999)),
            "fraction_bounded_ray": float(np.mean(fraction_trace < 0.999)),
            "minimum_reliability": float(np.min(reliability_trace)),
        }
    return estimates, covariances


def ukf_metric_sequence(
    measured: np.ndarray,
    transition: np.ndarray,
    process_scale: float,
    cubic: float,
    measurement_covariance: np.ndarray,
):
    """Positive-weight sigma-point baseline with a general fixed metric."""
    trajectories, steps, dimension = measured.shape
    mean = np.zeros((trajectories, dimension))
    covariance = np.repeat(np.eye(dimension)[None, :, :], trajectories, axis=0)
    estimates = np.zeros_like(measured)
    covariances = np.zeros((trajectories, steps, dimension, dimension))
    process_covariance = process_scale**2 * np.eye(dimension)
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
            [
                mean[:, None, :],
                mean[:, None, :] + offset,
                mean[:, None, :] - offset,
            ],
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


def correlated_system_paths(
    rng: np.random.Generator,
    regime: str,
    trajectories: int,
    steps: int,
    transition: np.ndarray,
    process_scale: float,
    cubic: float,
    correlation: np.ndarray,
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
    root = np.linalg.cholesky(correlation)
    noise = np.einsum("...i,ji->...j", noise, root)
    return state, observation(state, cubic) + noise


def correlation_error(estimated: np.ndarray, truth: np.ndarray, burn: int = 15):
    active = estimated[:, burn:]
    return float(
        np.sqrt(np.mean((active - truth[None, None, :, :]) ** 2))
    )


def theoretical_raw_moment(
    rng: np.random.Generator,
    correlation: np.ndarray,
    state_covariance: np.ndarray,
    count: int,
):
    """Population sanity fixture for E[nu nu' - HPH] / sigma^2."""
    dimension = len(correlation)
    state = rng.multivariate_normal(np.zeros(dimension), state_covariance, count)
    noise = rng.multivariate_normal(np.zeros(dimension), correlation, count)
    innovation = state + noise
    outer = np.einsum("ni,nj->nij", innovation, innovation)
    return np.mean(outer - state_covariance[None], axis=0)
