"""Scoring-Rule and Reporting-Contract Designer (SRCD) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Sequence

import numpy as np
from scipy.optimize import brentq


Target = Literal["MEAN", "QUANTILE", "EXPECTILE", "BINARY_PROBABILITY"]


@dataclass(frozen=True)
class ReportingContract:
    target: str
    level: float | None
    elicited_report: float
    best_raw_score_report: float
    best_payment_report: float
    raw_optimal_min: float
    raw_optimal_max: float
    payment_optimal_min: float
    payment_optimal_max: float
    expected_loss_at_truth: float
    expected_payment_at_truth: float
    maximum_expected_payment: float
    properness_verified_on_grid: bool
    strict_incentive_preserved_after_payment_clipping: bool
    payment_clipping_active: bool
    score_name: str
    report_grid_size: int

    def to_dict(self) -> dict:
        return asdict(self)


def _expectile(outcomes: np.ndarray, tau: float) -> float:
    low, high = float(np.min(outcomes)), float(np.max(outcomes))
    if low == high:
        return low

    def equation(report: float) -> float:
        residual = outcomes - report
        weights = np.where(residual >= 0, tau, 1.0 - tau)
        return float(np.mean(weights * residual))

    return float(brentq(equation, low, high))


def _loss(outcomes: np.ndarray, reports: np.ndarray, target: Target, level: float | None) -> np.ndarray:
    residual = outcomes[:, None] - reports[None, :]
    if target in ("MEAN", "BINARY_PROBABILITY"):
        return residual**2
    if target == "QUANTILE":
        return np.where(residual >= 0, level * residual, (level - 1.0) * residual)
    if target == "EXPECTILE":
        weights = np.where(residual >= 0, level, 1.0 - level)
        return weights * residual**2
    raise ValueError(f"unknown target: {target}")


def design_reporting_contract(
    outcomes: Sequence[float],
    target: Target,
    *,
    level: float | None = None,
    report_grid: Sequence[float] | None = None,
    base_payment: float = 0.0,
    loss_multiplier: float = 1.0,
    payment_floor: float | None = None,
    payment_ceiling: float | None = None,
    optimum_tolerance: float = 1e-9,
) -> ReportingContract:
    """Construct and empirically verify a target-eliciting score/payment contract."""

    values = np.asarray(outcomes, dtype=float)
    if values.ndim != 1 or values.size < 2 or not np.all(np.isfinite(values)):
        raise ValueError("outcomes must be a finite one-dimensional sample with at least two values")
    if target in ("QUANTILE", "EXPECTILE"):
        if level is None or not 0 < level < 1:
            raise ValueError("quantile and expectile levels must lie strictly between zero and one")
    elif level is not None:
        raise ValueError("level applies only to quantile or expectile targets")
    if target == "BINARY_PROBABILITY" and not np.all(np.isin(values, [0.0, 1.0])):
        raise ValueError("binary-probability outcomes must be zero or one")
    if not np.isfinite(base_payment) or not np.isfinite(loss_multiplier) or loss_multiplier <= 0:
        raise ValueError("base payment must be finite and loss multiplier positive")
    if payment_floor is not None and not np.isfinite(payment_floor):
        raise ValueError("payment floor must be finite")
    if payment_ceiling is not None and not np.isfinite(payment_ceiling):
        raise ValueError("payment ceiling must be finite")
    if payment_floor is not None and payment_ceiling is not None and payment_floor > payment_ceiling:
        raise ValueError("payment floor cannot exceed payment ceiling")

    if target in ("MEAN", "BINARY_PROBABILITY"):
        truth = float(np.mean(values))
        score_name = "BRIER" if target == "BINARY_PROBABILITY" else "SQUARED_ERROR"
    elif target == "QUANTILE":
        truth = float(np.quantile(values, level, method="inverted_cdf"))
        score_name = "PINBALL"
    else:
        truth = _expectile(values, level)
        score_name = "ASYMMETRIC_SQUARED_ERROR"

    if report_grid is None:
        lower, upper = (0.0, 1.0) if target == "BINARY_PROBABILITY" else (float(np.min(values)), float(np.max(values)))
        grid = np.linspace(lower, upper, 2001)
    else:
        grid = np.asarray(report_grid, dtype=float)
        if grid.ndim != 1 or grid.size < 2 or not np.all(np.isfinite(grid)):
            raise ValueError("report_grid must contain at least two finite values")
    grid = np.unique(np.append(grid, truth))
    expected_loss = np.mean(_loss(values, grid, target, level), axis=0)
    raw_minimum = float(np.min(expected_loss))
    raw_mask = expected_loss <= raw_minimum + optimum_tolerance
    raw_reports = grid[raw_mask]
    raw_best = float(raw_reports[np.argmin(np.abs(raw_reports - truth))])

    payments = base_payment - loss_multiplier * _loss(values, grid, target, level)
    clipping = payment_floor is not None or payment_ceiling is not None
    if payment_floor is not None:
        payments = np.maximum(payments, payment_floor)
    if payment_ceiling is not None:
        payments = np.minimum(payments, payment_ceiling)
    expected_payment = np.mean(payments, axis=0)
    maximum_payment = float(np.max(expected_payment))
    payment_mask = expected_payment >= maximum_payment - optimum_tolerance
    payment_reports = grid[payment_mask]
    payment_best = float(payment_reports[np.argmin(np.abs(payment_reports - truth))])
    truth_index = int(np.where(grid == truth)[0][0])
    proper = bool(expected_loss[truth_index] <= raw_minimum + optimum_tolerance)
    grid_step = float(np.min(np.diff(grid))) if grid.size > 1 else 0.0
    strict_preserved = bool(
        expected_payment[truth_index] >= maximum_payment - optimum_tolerance
        and payment_reports[-1] - payment_reports[0] <= max(2 * grid_step, optimum_tolerance)
    )
    return ReportingContract(
        target, level, truth, raw_best, payment_best,
        float(raw_reports[0]), float(raw_reports[-1]),
        float(payment_reports[0]), float(payment_reports[-1]),
        float(expected_loss[truth_index]), float(expected_payment[truth_index]), maximum_payment,
        proper, strict_preserved, clipping, score_name, int(grid.size),
    )
