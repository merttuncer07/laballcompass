"""Differentiation-Free Dynamic Parameter Estimator (DFDPE) v0.1.

The estimator fits the continuous-time model

    dy/dt = persistence * y + input_gain * u + drift

without numerically differentiating the measured output.  It multiplies the
equation by smooth window functions and moves the derivative onto those known
functions by integration by parts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class WindowEquation:
    start_time: float
    end_time: float
    integrated_output: float
    integrated_input: float
    integrated_constant: float
    derivative_free_target: float
    residual: float
    robust_weight: float


@dataclass(frozen=True)
class DynamicParameterEstimate:
    persistence: float
    input_gain: float
    drift: float
    standard_errors: tuple[float, float, float]
    integral_residual_rmse: float
    validation_rollout_rmse: float | None


@dataclass(frozen=True)
class FiniteDifferenceBaseline:
    persistence: float
    input_gain: float
    drift: float
    validation_rollout_rmse: float | None


@dataclass(frozen=True)
class DynamicEstimationResult:
    estimate: DynamicParameterEstimate | None
    finite_difference_baseline: FiniteDifferenceBaseline | None
    equations: tuple[WindowEquation, ...]
    design_rank: int
    design_condition_number: float
    number_of_windows: int
    derivative_taken_from_observed_data: bool
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_affine_dynamics(
    times: Sequence[float],
    inputs: Sequence[float],
    initial_output: float,
    parameters: Sequence[float],
) -> np.ndarray:
    """Roll out the fitted ODE using a stable trapezoidal step."""

    t = np.asarray(times, dtype=float)
    u = np.asarray(inputs, dtype=float)
    theta = np.asarray(parameters, dtype=float)
    if t.ndim != 1 or u.shape != t.shape or theta.shape != (3,):
        raise ValueError("times/inputs must be equal vectors and parameters must have length three")
    if t.size < 2 or not np.all(np.diff(t) > 0) or not np.all(np.isfinite(t)):
        raise ValueError("times must be finite and strictly increasing")
    if not np.all(np.isfinite(u)) or not np.isfinite(initial_output) or not np.all(np.isfinite(theta)):
        raise ValueError("simulation values must be finite")
    a, b, c = theta
    output = np.empty(t.size, dtype=float)
    output[0] = float(initial_output)
    for index, dt in enumerate(np.diff(t)):
        denominator = 1.0 - 0.5 * dt * a
        if abs(denominator) < 1e-12:
            raise ValueError("trapezoidal step is singular for these parameters")
        output[index + 1] = (
            output[index] * (1.0 + 0.5 * dt * a)
            + dt * (0.5 * b * (u[index] + u[index + 1]) + c)
        ) / denominator
    return output


def _weighted_fit(design: np.ndarray, target: np.ndarray, robust: bool) -> tuple[np.ndarray, np.ndarray]:
    weights = np.ones(target.size, dtype=float)
    estimate = np.linalg.lstsq(design, target, rcond=None)[0]
    if robust:
        for _ in range(30):
            residual = target - design @ estimate
            center = float(np.median(residual))
            scale = 1.4826 * float(np.median(np.abs(residual - center))) + 1e-12
            cutoff = 1.5 * scale
            absolute = np.abs(residual - center)
            new_weights = np.ones_like(weights)
            mask = absolute > cutoff
            new_weights[mask] = cutoff / absolute[mask]
            root = np.sqrt(new_weights)
            updated = np.linalg.lstsq(design * root[:, None], target * root, rcond=None)[0]
            if np.linalg.norm(updated - estimate) <= 1e-10 * (1.0 + np.linalg.norm(estimate)):
                estimate, weights = updated, new_weights
                break
            estimate, weights = updated, new_weights
    return estimate, weights


def _validation_rmse(
    theta: np.ndarray,
    validation_times: np.ndarray | None,
    validation_outputs: np.ndarray | None,
    validation_inputs: np.ndarray | None,
) -> float | None:
    if validation_times is None:
        return None
    prediction = simulate_affine_dynamics(
        validation_times, validation_inputs, float(validation_outputs[0]), theta
    )
    return float(np.sqrt(np.mean((prediction - validation_outputs) ** 2)))


def estimate_affine_dynamics(
    times: Sequence[float],
    observed_outputs: Sequence[float],
    inputs: Sequence[float],
    *,
    window_duration: float,
    window_step: float,
    robust: bool = True,
    validation_times: Sequence[float] | None = None,
    validation_outputs: Sequence[float] | None = None,
    validation_inputs: Sequence[float] | None = None,
    maximum_condition_number: float = 1e8,
) -> DynamicEstimationResult:
    """Estimate dynamic parameters without differentiating observed outputs.

    A sin² modulation function is placed in every overlapping window.  Its
    endpoint values are zero, so integration by parts gives a linear equation
    whose target is ``-integral(phi' * observed_output)``.
    """

    t = np.asarray(times, dtype=float)
    y = np.asarray(observed_outputs, dtype=float)
    u = np.asarray(inputs, dtype=float)
    if t.ndim != 1 or y.shape != t.shape or u.shape != t.shape or t.size < 8:
        raise ValueError("training times, outputs, and inputs must be equal vectors of length >= 8")
    if not all(np.all(np.isfinite(value)) for value in (t, y, u)) or not np.all(np.diff(t) > 0):
        raise ValueError("training data must be finite with strictly increasing times")
    if window_duration <= 0 or window_step <= 0 or window_duration > t[-1] - t[0]:
        raise ValueError("window duration and step must be positive and fit inside the sample")
    if maximum_condition_number <= 1:
        raise ValueError("maximum_condition_number must exceed one")

    validation_arrays = (validation_times, validation_outputs, validation_inputs)
    if any(value is not None for value in validation_arrays):
        if not all(value is not None for value in validation_arrays):
            raise ValueError("all three validation arrays must be supplied together")
        vt = np.asarray(validation_times, dtype=float)
        vy = np.asarray(validation_outputs, dtype=float)
        vu = np.asarray(validation_inputs, dtype=float)
        if vt.ndim != 1 or vy.shape != vt.shape or vu.shape != vt.shape or vt.size < 2:
            raise ValueError("validation arrays must be equal vectors of length >= 2")
        if not all(np.all(np.isfinite(value)) for value in (vt, vy, vu)) or not np.all(np.diff(vt) > 0):
            raise ValueError("validation data must be finite with increasing times")
    else:
        vt = vy = vu = None

    rows: list[list[float]] = []
    targets: list[float] = []
    bounds: list[tuple[float, float]] = []
    start = float(t[0])
    while start + window_duration <= t[-1] + 1e-12:
        end = start + window_duration
        indices = np.flatnonzero((t >= start - 1e-12) & (t <= end + 1e-12))
        if indices.size >= 5:
            local_t = t[indices]
            span = float(local_t[-1] - local_t[0])
            if span >= 0.9 * window_duration:
                phase = (local_t - local_t[0]) / span
                phi = np.sin(np.pi * phase) ** 2
                dphi = (np.pi / span) * np.sin(2.0 * np.pi * phase)
                row = [
                    float(np.trapezoid(phi * y[indices], local_t)),
                    float(np.trapezoid(phi * u[indices], local_t)),
                    float(np.trapezoid(phi, local_t)),
                ]
                target = -float(np.trapezoid(dphi * y[indices], local_t))
                rows.append(row)
                targets.append(target)
                bounds.append((float(local_t[0]), float(local_t[-1])))
        start += window_step
    if len(rows) < 3:
        raise ValueError("window settings produced fewer than three usable equations")

    design = np.asarray(rows)
    target = np.asarray(targets)
    rank = int(np.linalg.matrix_rank(design))
    condition = float(np.linalg.cond(design))
    if rank < 3 or not np.isfinite(condition) or condition > maximum_condition_number:
        return DynamicEstimationResult(
            estimate=None,
            finite_difference_baseline=None,
            equations=tuple(
                WindowEquation(*window, *map(float, row), float(goal), float("nan"), 0.0)
                for window, row, goal in zip(bounds, design, target)
            ),
            design_rank=rank,
            design_condition_number=condition,
            number_of_windows=len(rows),
            derivative_taken_from_observed_data=False,
            status="UNDEREXCITED_PARAMETERS_NOT_IDENTIFIABLE",
        )

    theta, weights = _weighted_fit(design, target, robust)
    residuals = target - design @ theta
    dof = max(1, len(target) - 3)
    weighted_design = design * np.sqrt(weights)[:, None]
    variance = float(np.sum(weights * residuals**2) / dof)
    covariance = variance * np.linalg.pinv(weighted_design.T @ weighted_design)
    standard_errors = np.sqrt(np.maximum(0.0, np.diag(covariance)))
    validation_rmse = _validation_rmse(theta, vt, vy, vu)

    # This baseline is reported as an audit contrast, not used by DFDPE.
    derivative = np.gradient(y, t)
    fd_design = np.column_stack((y, u, np.ones_like(y)))
    fd_theta = np.linalg.lstsq(fd_design, derivative, rcond=None)[0]
    fd_validation_rmse = _validation_rmse(fd_theta, vt, vy, vu)
    equation_records = tuple(
        WindowEquation(
            start_time=window[0],
            end_time=window[1],
            integrated_output=float(row[0]),
            integrated_input=float(row[1]),
            integrated_constant=float(row[2]),
            derivative_free_target=float(goal),
            residual=float(residual),
            robust_weight=float(weight),
        )
        for window, row, goal, residual, weight in zip(bounds, design, target, residuals, weights)
    )
    return DynamicEstimationResult(
        estimate=DynamicParameterEstimate(
            persistence=float(theta[0]),
            input_gain=float(theta[1]),
            drift=float(theta[2]),
            standard_errors=tuple(map(float, standard_errors)),
            integral_residual_rmse=float(np.sqrt(np.mean(residuals**2))),
            validation_rollout_rmse=validation_rmse,
        ),
        finite_difference_baseline=FiniteDifferenceBaseline(
            persistence=float(fd_theta[0]),
            input_gain=float(fd_theta[1]),
            drift=float(fd_theta[2]),
            validation_rollout_rmse=fd_validation_rmse,
        ),
        equations=equation_records,
        design_rank=rank,
        design_condition_number=condition,
        number_of_windows=len(rows),
        derivative_taken_from_observed_data=False,
        status="DYNAMIC_PARAMETERS_ESTIMATED_WITHOUT_DATA_DIFFERENTIATION",
    )
