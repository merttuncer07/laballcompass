"""Decision-focused Hedge Covariance Calibrator (DHCC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class HedgeCandidate:
    ridge: float
    hedge_coefficients: tuple[float, ...]
    intercept: float
    training_residual_variance: float
    validation_residual_variance: float
    turnover: float
    validation_decision_loss: float
    hedge_condition_number: float


@dataclass(frozen=True)
class HedgeCalibrationResult:
    selected: HedgeCandidate
    candidates: tuple[HedgeCandidate, ...]
    unhedged_validation_variance: float
    unregularized_validation_variance: float | None
    variance_reduction_fraction_vs_unhedged: float
    variance_reduction_fraction_vs_unregularized: float | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def calibrate_hedge_covariance(
    target_training_returns: Sequence[float],
    hedge_training_returns: Sequence[Sequence[float]],
    target_validation_returns: Sequence[float],
    hedge_validation_returns: Sequence[Sequence[float]],
    *,
    ridge_grid: Sequence[float],
    reference_coefficients: Sequence[float] | None = None,
    turnover_penalty: float = 0.0,
) -> HedgeCalibrationResult:
    """Choose covariance regularization by realized hedge loss, not matrix fit alone."""

    y_train = np.asarray(target_training_returns, dtype=float)
    x_train = np.asarray(hedge_training_returns, dtype=float)
    y_val = np.asarray(target_validation_returns, dtype=float)
    x_val = np.asarray(hedge_validation_returns, dtype=float)
    if y_train.ndim != 1 or y_val.ndim != 1 or x_train.ndim != 2 or x_val.ndim != 2:
        raise ValueError("targets must be vectors and hedge returns must be matrices")
    if x_train.shape[0] != y_train.size or x_val.shape[0] != y_val.size or x_train.shape[1] != x_val.shape[1]:
        raise ValueError("target and hedge sample dimensions must match")
    if y_train.size < 3 or y_val.size < 2 or x_train.shape[1] < 1 or not all(np.all(np.isfinite(a)) for a in (y_train, x_train, y_val, x_val)):
        raise ValueError("return samples must be finite and sufficiently large")
    grid = sorted(set(map(float, ridge_grid)))
    if not grid or min(grid) < 0 or turnover_penalty < 0:
        raise ValueError("ridge values and turnover_penalty must be nonnegative")
    p = x_train.shape[1]
    reference = np.zeros(p) if reference_coefficients is None else np.asarray(reference_coefficients, dtype=float)
    if reference.shape != (p,) or not np.all(np.isfinite(reference)):
        raise ValueError("reference_coefficients must match hedge columns")

    x_mean = x_train.mean(axis=0); y_mean = float(y_train.mean())
    xc = x_train - x_mean; yc = y_train - y_mean
    hedge_covariance = xc.T @ xc / (y_train.size - 1)
    cross_covariance = xc.T @ yc / (y_train.size - 1)
    scale = float(np.trace(hedge_covariance) / p)
    if scale <= 0:
        raise ValueError("hedge returns have zero covariance scale")
    candidates: list[HedgeCandidate] = []
    for ridge in grid:
        regularized = hedge_covariance + ridge * scale * np.eye(p)
        try:
            coefficients = np.linalg.solve(regularized, cross_covariance)
        except np.linalg.LinAlgError:
            continue
        intercept = y_mean - float(x_mean @ coefficients)
        train_residual = y_train - (intercept + x_train @ coefficients)
        validation_residual = y_val - (intercept + x_val @ coefficients)
        train_variance = float(np.var(train_residual, ddof=1))
        validation_variance = float(np.var(validation_residual, ddof=1))
        turnover = float(np.sum(np.abs(coefficients - reference)))
        decision_loss = validation_variance + turnover_penalty * turnover
        candidates.append(HedgeCandidate(
            ridge=ridge,
            hedge_coefficients=tuple(map(float, coefficients)),
            intercept=float(intercept),
            training_residual_variance=train_variance,
            validation_residual_variance=validation_variance,
            turnover=turnover,
            validation_decision_loss=float(decision_loss),
            hedge_condition_number=float(np.linalg.cond(regularized)),
        ))
    if not candidates:
        raise RuntimeError("no hedge candidate could be solved")
    selected = min(candidates, key=lambda candidate: (candidate.validation_decision_loss, candidate.ridge))
    unhedged = float(np.var(y_val, ddof=1))
    unregularized = next((c.validation_residual_variance for c in candidates if c.ridge == 0.0), None)
    vs_unhedged = float(1.0 - selected.validation_residual_variance / unhedged) if unhedged > 0 else 0.0
    vs_raw = None if unregularized is None or unregularized <= 0 else float(1.0 - selected.validation_residual_variance / unregularized)
    return HedgeCalibrationResult(
        selected=selected,
        candidates=tuple(candidates),
        unhedged_validation_variance=unhedged,
        unregularized_validation_variance=unregularized,
        variance_reduction_fraction_vs_unhedged=vs_unhedged,
        variance_reduction_fraction_vs_unregularized=vs_raw,
        status="DECISION_FOCUSED_HEDGE_CALIBRATED",
    )
