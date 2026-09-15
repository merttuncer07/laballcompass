"""Orthogonal Target Estimator, built from IM-256 -> IM-307."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class OrthogonalEstimate:
    target: float
    standard_error: float
    confidence_low_95: float
    confidence_high_95: float
    observations: int
    folds: int
    residual_treatment_variance: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ridge_predict(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, ridge: float) -> np.ndarray:
    train_aug = np.column_stack([np.ones(len(train_x)), train_x])
    test_aug = np.column_stack([np.ones(len(test_x)), test_x])
    penalty = np.eye(train_aug.shape[1]) * ridge
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(train_aug.T @ train_aug + penalty, train_aug.T @ train_y)
    return test_aug @ coefficients


def estimate_from_nuisance_predictions(
    treatment: Sequence[float],
    outcome: Sequence[float],
    treatment_prediction: Sequence[float],
    outcome_prediction: Sequence[float],
    folds: int = 1,
) -> OrthogonalEstimate:
    d = np.asarray(treatment, dtype=float)
    y = np.asarray(outcome, dtype=float)
    m = np.asarray(treatment_prediction, dtype=float)
    ell = np.asarray(outcome_prediction, dtype=float)
    if not (d.shape == y.shape == m.shape == ell.shape) or d.ndim != 1:
        raise ValueError("Treatment, outcome, and nuisance predictions must be equal-length vectors")
    v = d - m
    u = y - ell
    denominator = float(v @ v)
    if denominator <= 1e-12:
        raise ValueError("Residual treatment variation is too small to identify the target")
    theta = float(v @ u / denominator)
    psi = v * (u - theta * v)
    n = len(d)
    mean_v2 = float(np.mean(v**2))
    standard_error = float(np.sqrt(np.mean(psi**2) / (mean_v2**2 * n)))
    return OrthogonalEstimate(
        target=theta,
        standard_error=standard_error,
        confidence_low_95=theta - 1.96 * standard_error,
        confidence_high_95=theta + 1.96 * standard_error,
        observations=n,
        folds=folds,
        residual_treatment_variance=mean_v2,
    )


class OrthogonalTargetEstimator:
    def __init__(self, folds: int = 5, ridge: float = 1e-6, seed: int = 20260825) -> None:
        if folds < 2:
            raise ValueError("folds must be at least two for cross-fitting")
        if ridge < 0:
            raise ValueError("ridge must be non-negative")
        self.folds = folds
        self.ridge = ridge
        self.seed = seed

    def fit(
        self,
        representation: Sequence[Sequence[float]],
        treatment: Sequence[float],
        outcome: Sequence[float],
    ) -> OrthogonalEstimate:
        X = np.asarray(representation, dtype=float)
        d = np.asarray(treatment, dtype=float)
        y = np.asarray(outcome, dtype=float)
        if X.ndim != 2 or len(X) != len(d) or len(d) != len(y):
            raise ValueError("Representation rows, treatment, and outcome must align")
        if len(X) < self.folds:
            raise ValueError("Observation count must be at least the number of folds")
        rng = np.random.default_rng(self.seed)
        order = rng.permutation(len(X))
        fold_indices = np.array_split(order, self.folds)
        treatment_prediction = np.empty(len(X))
        outcome_prediction = np.empty(len(X))
        all_indices = np.arange(len(X))
        for test_index in fold_indices:
            train_mask = np.ones(len(X), dtype=bool)
            train_mask[test_index] = False
            train_index = all_indices[train_mask]
            treatment_prediction[test_index] = _ridge_predict(
                X[train_index], d[train_index], X[test_index], self.ridge
            )
            outcome_prediction[test_index] = _ridge_predict(
                X[train_index], y[train_index], X[test_index], self.ridge
            )
        return estimate_from_nuisance_predictions(
            d, y, treatment_prediction, outcome_prediction, folds=self.folds
        )
