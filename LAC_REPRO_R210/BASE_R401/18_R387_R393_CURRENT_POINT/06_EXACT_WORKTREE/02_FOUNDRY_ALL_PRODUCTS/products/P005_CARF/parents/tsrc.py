"""Target-Sufficient Reduction Certifier, built from IM-124 -> IM-256."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    coefficient: float
    deletion_deviation_bound: float
    removable_cost: float = 1.0

    @property
    def target_error_bound(self) -> float:
        return abs(self.coefficient) * self.deletion_deviation_bound


@dataclass(frozen=True)
class ReductionCertificate:
    deleted_features: tuple[str, ...]
    retained_features: tuple[str, ...]
    removable_cost_saved: float
    score_error_bound: float
    protected_margin: float
    remaining_margin_certificate: float
    action_invariant: bool
    actual_max_score_change_on_evaluation: float | None = None
    observed_action_changes: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TargetSufficientReductionCertifier:
    def __init__(
        self,
        features: Sequence[FeatureSpec],
        thresholds: Sequence[float] = (0.0,),
    ) -> None:
        if not features:
            raise ValueError("At least one feature is required")
        self.features = tuple(features)
        self.thresholds = np.asarray(thresholds, dtype=float)
        if self.thresholds.ndim != 1 or len(self.thresholds) == 0:
            raise ValueError("At least one threshold is required")
        if np.any(np.diff(self.thresholds) <= 0):
            raise ValueError("Thresholds must be strictly increasing")
        if any(feature.deletion_deviation_bound < 0 for feature in features):
            raise ValueError("Deletion deviation bounds must be non-negative")
        if any(feature.removable_cost < 0 for feature in features):
            raise ValueError("Removable costs must be non-negative")

    def optimize(self, protected_margin: float, reserve: float = 0.0) -> ReductionCertificate:
        if protected_margin <= 0:
            raise ValueError("protected_margin must be positive")
        if reserve < 0 or reserve >= protected_margin:
            raise ValueError("reserve must satisfy 0 <= reserve < protected_margin")
        error_budget = protected_margin - reserve
        contributions = np.array([feature.target_error_bound for feature in self.features])
        savings = np.array([feature.removable_cost for feature in self.features])
        result = milp(
            c=-savings,
            integrality=np.ones(len(self.features)),
            bounds=Bounds(np.zeros(len(self.features)), np.ones(len(self.features))),
            constraints=LinearConstraint(contributions, -np.inf, error_budget),
            options={"disp": False},
        )
        if not result.success:
            raise RuntimeError(f"Feature-deletion optimization failed: {result.message}")
        deleted_mask = np.asarray(result.x) > 0.5
        error_bound = float(contributions[deleted_mask].sum())
        saved = float(savings[deleted_mask].sum())
        remaining = protected_margin - error_bound
        return ReductionCertificate(
            deleted_features=tuple(
                feature.name for feature, deleted in zip(self.features, deleted_mask) if deleted
            ),
            retained_features=tuple(
                feature.name for feature, deleted in zip(self.features, deleted_mask) if not deleted
            ),
            removable_cost_saved=saved,
            score_error_bound=error_bound,
            protected_margin=protected_margin,
            remaining_margin_certificate=remaining,
            action_invariant=error_bound < protected_margin,
        )

    def evaluate(
        self,
        certificate: ReductionCertificate,
        values: Sequence[Sequence[float]],
        baselines: Sequence[float] | None = None,
        intercept: float = 0.0,
    ) -> ReductionCertificate:
        X = np.asarray(values, dtype=float)
        if X.ndim != 2 or X.shape[1] != len(self.features):
            raise ValueError("Evaluation matrix column count must match features")
        baseline = (
            np.zeros(len(self.features))
            if baselines is None
            else np.asarray(baselines, dtype=float)
        )
        if baseline.shape != (len(self.features),):
            raise ValueError("Baseline length must match features")
        weights = np.array([feature.coefficient for feature in self.features])
        full_scores = X @ weights + intercept
        reduced = X.copy()
        deleted_names = set(certificate.deleted_features)
        for index, feature in enumerate(self.features):
            if feature.name in deleted_names:
                observed_deviation = float(np.max(np.abs(X[:, index] - baseline[index])))
                if observed_deviation > feature.deletion_deviation_bound + 1e-12:
                    raise ValueError(
                        f"Evaluation leaves declared deletion shell for {feature.name}: "
                        f"observed {observed_deviation}, bound {feature.deletion_deviation_bound}"
                    )
                reduced[:, index] = baseline[index]
        reduced_scores = reduced @ weights + intercept
        full_actions = np.searchsorted(self.thresholds, full_scores, side="right")
        reduced_actions = np.searchsorted(self.thresholds, reduced_scores, side="right")
        return ReductionCertificate(
            **{
                **certificate.as_dict(),
                "actual_max_score_change_on_evaluation": float(
                    np.max(np.abs(full_scores - reduced_scores))
                ),
                "observed_action_changes": int(np.sum(full_actions != reduced_actions)),
            }
        )

    def margin_on_values(
        self, values: Sequence[Sequence[float]], intercept: float = 0.0
    ) -> float:
        X = np.asarray(values, dtype=float)
        weights = np.array([feature.coefficient for feature in self.features])
        scores = X @ weights + intercept
        return float(np.min(np.abs(scores[:, None] - self.thresholds[None, :])))
