"""Support-Aware Covariance and Precision Service (SACPS) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class CovarianceDecisionResult:
    selected_shrinkage: float
    covariance: tuple[tuple[float, ...], ...]
    precision: tuple[tuple[float, ...], ...]
    minimum_eigenvalue: float
    condition_number: float
    raw_sample_condition_number: float
    unsupported_max_absolute_covariance: float
    gaussian_validation_scores: tuple[tuple[float, float], ...]
    minimum_variance_weights: tuple[float, ...]
    predicted_portfolio_variance: float
    realized_holdout_variance: float | None
    raw_sample_realized_holdout_variance: float | None
    realized_risk_change_fraction_vs_raw: float | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _minimum_variance_weights(covariance: np.ndarray) -> np.ndarray:
    precision = np.linalg.inv(covariance)
    ones = np.ones(covariance.shape[0])
    numerator = precision @ ones
    denominator = float(ones @ numerator)
    if abs(denominator) < 1e-14:
        raise ValueError("minimum-variance budget constraint is degenerate")
    return numerator / denominator


def estimate_support_aware_covariance(
    training_returns: Sequence[Sequence[float]],
    support_mask: Sequence[Sequence[bool]],
    *,
    holdout_returns: Sequence[Sequence[float]] | None = None,
    validation_returns: Sequence[Sequence[float]] | None = None,
    shrinkage_grid: Sequence[float] = tuple(np.linspace(0.0, 1.0, 21)),
    eigenvalue_floor: float = 1e-8,
    maximum_condition_number: float = 1e8,
) -> CovarianceDecisionResult:
    """Fit on training data, optionally tune on validation, evaluate only on holdout.

    With no validation, choose the smallest numerically admissible shrinkage.
    The legacy gaussian_validation_scores field then contains the shrinkage
    selection objective, not held-out Gaussian scores.
    """

    train = np.asarray(training_returns, dtype=float)
    if train.ndim != 2 or train.shape[0] < 3 or train.shape[1] < 2 or not np.all(np.isfinite(train)):
        raise ValueError("training_returns must be a finite case-by-variable matrix")
    p = train.shape[1]
    mask = np.asarray(support_mask, dtype=bool)
    if mask.shape != (p, p) or not np.array_equal(mask, mask.T) or not np.all(np.diag(mask)):
        raise ValueError("support_mask must be symmetric, square, and include the diagonal")
    grid = sorted(set(map(float, shrinkage_grid)))
    if not grid or not np.all(np.isfinite(grid)) or min(grid) < 0 or max(grid) > 1 or not np.isfinite(eigenvalue_floor) or not np.isfinite(maximum_condition_number) or eigenvalue_floor <= 0 or maximum_condition_number <= 1:
        raise ValueError("invalid shrinkage grid or numerical thresholds")
    holdout = None if holdout_returns is None else np.asarray(holdout_returns, dtype=float)
    if holdout is not None and (holdout.ndim != 2 or holdout.shape[0] < 2 or holdout.shape[1] != p or not np.all(np.isfinite(holdout))):
        raise ValueError("holdout_returns must be finite and have the same variables")

    validation = None if validation_returns is None else np.asarray(validation_returns, dtype=float)
    if validation is not None and (validation.ndim != 2 or validation.shape[0] < 2 or validation.shape[1] != p or not np.all(np.isfinite(validation))):
        raise ValueError("validation_returns must be finite and have the same variables")
    if validation is not None and holdout is not None and (np.shares_memory(validation, holdout) or np.array_equal(validation, holdout)):
        raise ValueError("validation and holdout must be separate data, not the same matrix")

    mean = train.mean(axis=0)
    centered = train - mean
    sample = centered.T @ centered / (train.shape[0] - 1)
    structured = np.where(mask, sample, 0.0)
    diagonal = np.diag(np.diag(sample))
    raw_condition = float(np.linalg.cond(sample))
    scores: list[tuple[float, float]] = []
    candidates: list[tuple[float, np.ndarray, float]] = []
    for shrinkage in grid:
        covariance = (1.0 - shrinkage) * structured + shrinkage * diagonal
        eigenvalues = np.linalg.eigvalsh(covariance)
        if float(eigenvalues[0]) < eigenvalue_floor:
            continue
        condition = float(eigenvalues[-1] / eigenvalues[0])
        if condition > maximum_condition_number:
            continue
        if validation is not None:
            validation_centered = validation - mean
            sign, logdet = np.linalg.slogdet(covariance)
            if sign <= 0:
                continue
            quadratic = np.einsum("ij,jk,ik->i", validation_centered, np.linalg.inv(covariance), validation_centered)
            score = float(logdet + np.mean(quadratic))
        else:
            score = shrinkage
        scores.append((shrinkage, score))
        candidates.append((score, covariance, shrinkage))
    if not candidates:
        raise RuntimeError("no positive-definite supported covariance found on the shrinkage grid")
    _, covariance, selected_shrinkage = min(candidates, key=lambda item: (item[0], item[2]))
    precision = np.linalg.inv(covariance)
    weights = _minimum_variance_weights(covariance)
    predicted = float(weights @ covariance @ weights)
    realized = raw_realized = change = None
    if holdout is not None:
        holdout_covariance = np.cov(holdout, rowvar=False, ddof=1)
        realized = float(weights @ holdout_covariance @ weights)
        try:
            raw_weights = _minimum_variance_weights(sample)
            raw_realized = float(raw_weights @ holdout_covariance @ raw_weights)
            change = None if raw_realized <= 0 else float(realized / raw_realized - 1.0)
        except (np.linalg.LinAlgError, ValueError):
            pass
    unsupported = np.logical_not(mask)
    unsupported_max = float(np.max(np.abs(covariance[unsupported]))) if np.any(unsupported) else 0.0
    return CovarianceDecisionResult(
        selected_shrinkage=float(selected_shrinkage),
        covariance=tuple(tuple(map(float, row)) for row in covariance),
        precision=tuple(tuple(map(float, row)) for row in precision),
        minimum_eigenvalue=float(np.linalg.eigvalsh(covariance)[0]),
        condition_number=float(np.linalg.cond(covariance)),
        raw_sample_condition_number=raw_condition,
        unsupported_max_absolute_covariance=unsupported_max,
        gaussian_validation_scores=tuple(scores),
        minimum_variance_weights=tuple(map(float, weights)),
        predicted_portfolio_variance=predicted,
        realized_holdout_variance=realized,
        raw_sample_realized_holdout_variance=raw_realized,
        realized_risk_change_fraction_vs_raw=change,
        status="SUPPORTED_COVARIANCE_AND_DECISION_READY",
    )
