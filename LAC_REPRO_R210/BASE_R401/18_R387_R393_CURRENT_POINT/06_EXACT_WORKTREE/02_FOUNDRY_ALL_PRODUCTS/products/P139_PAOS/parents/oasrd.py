"""Operator-Averaging Stabilizer with Residual Diagnostics (OASRD) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass(frozen=True)
class AveragingRun:
    alpha: float
    converged: bool
    iterations: int
    final_state: tuple[float, ...]
    final_fixed_point_residual: float
    minimum_fixed_point_residual: float
    maximum_state_norm: float
    late_residual_ratio: float | None
    state_history: tuple[tuple[float, ...], ...]
    residual_history: tuple[float, ...]
    status: str


@dataclass(frozen=True)
class AveragingSelection:
    selected: AveragingRun
    runs: tuple[AveragingRun, ...]
    direct_iteration: AveragingRun | None
    direct_to_selected_residual_ratio: float | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def run_averaged_operator(
    operator: Callable[[np.ndarray], Sequence[float]],
    initial_state: Sequence[float],
    *,
    alpha: float,
    maximum_iterations: int = 500,
    residual_tolerance: float = 1e-8,
    divergence_norm: float = 1e12,
) -> AveragingRun:
    """Iterate x <- (1-alpha)x + alpha T(x) and retain fixed-point residuals."""

    x = np.asarray(initial_state, dtype=float)
    if x.ndim != 1 or x.size < 1 or not np.all(np.isfinite(x)):
        raise ValueError("initial_state must be a finite vector")
    if not 0 < alpha <= 1 or not isinstance(maximum_iterations, int) or maximum_iterations < 1 or residual_tolerance < 0 or divergence_norm <= 0:
        raise ValueError("alpha must be in (0,1] and iteration controls valid")
    history = [tuple(map(float, x))]; residuals = []; maximum_norm = float(np.linalg.norm(x))
    converged = False; status = "MAXIMUM_ITERATIONS_REACHED"
    for iteration in range(maximum_iterations + 1):
        tx = np.asarray(operator(x.copy()), dtype=float)
        if tx.shape != x.shape or not np.all(np.isfinite(tx)):
            residuals.append(float("inf"))
            status = "OPERATOR_RETURNED_INVALID_STATE"; break
        residual = float(np.linalg.norm(tx - x)); residuals.append(residual)
        if residual <= residual_tolerance:
            converged = True; status = "FIXED_POINT_CONVERGED"; break
        if iteration == maximum_iterations:
            break
        x = (1.0 - alpha) * x + alpha * tx
        norm = float(np.linalg.norm(x)); maximum_norm = max(maximum_norm, norm)
        history.append(tuple(map(float, x)))
        if not np.all(np.isfinite(x)) or norm > divergence_norm:
            status = "ITERATION_DIVERGED"; break
    tail = residuals[-11:]
    ratios = [b / a for a, b in zip(tail[:-1], tail[1:]) if a > 1e-30]
    late_ratio = None if not ratios else float(np.median(ratios))
    return AveragingRun(
        alpha=float(alpha), converged=converged,
        iterations=len(history) - 1,
        final_state=tuple(map(float, x)),
        final_fixed_point_residual=float(residuals[-1]),
        minimum_fixed_point_residual=float(min(residuals)),
        maximum_state_norm=maximum_norm,
        late_residual_ratio=late_ratio,
        state_history=tuple(history), residual_history=tuple(residuals), status=status,
    )


def select_operator_averaging(
    operator: Callable[[np.ndarray], Sequence[float]],
    initial_state: Sequence[float],
    alpha_candidates: Sequence[float],
    **run_parameters,
) -> AveragingSelection:
    """Choose the fastest converged averaged operator, retaining all unsuccessful runs."""

    alphas = sorted(set(map(float, alpha_candidates)), reverse=True)
    if not alphas or min(alphas) <= 0 or max(alphas) > 1:
        raise ValueError("alpha_candidates must lie in (0,1]")
    runs = tuple(run_averaged_operator(operator, initial_state, alpha=alpha, **run_parameters) for alpha in alphas)
    converged = [run for run in runs if run.converged]
    if converged:
        selected = min(converged, key=lambda run: (run.iterations, run.final_fixed_point_residual, -run.alpha))
        status = "CONVERGENT_AVERAGING_PARAMETER_SELECTED"
    else:
        selected = min(runs, key=lambda run: (run.minimum_fixed_point_residual, run.final_fixed_point_residual))
        status = "NO_CANDIDATE_CONVERGED_BEST_RESIDUAL_RETURNED"
    direct = next((run for run in runs if run.alpha == 1.0), None)
    ratio = None
    if direct is not None and selected.final_fixed_point_residual > 0:
        ratio = float(direct.final_fixed_point_residual / selected.final_fixed_point_residual)
    return AveragingSelection(selected, runs, direct, ratio, status)
