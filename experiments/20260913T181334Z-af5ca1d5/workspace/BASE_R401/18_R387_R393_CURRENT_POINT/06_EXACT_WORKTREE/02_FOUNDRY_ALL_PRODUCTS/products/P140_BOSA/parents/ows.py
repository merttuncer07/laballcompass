"""Overlap-aware Weight Stabilizer, built from IM-274 -> IM-290."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class SupportAudit:
    observations: int
    effective_sample_size: float
    effective_sample_fraction: float
    max_normalized_weight: float
    top_one_percent_weight_mass: float
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StabilizedEstimate:
    raw_estimate: float
    stabilized_estimate: float
    selected_cap: float
    clipped_fraction: float
    effective_sample_size_before: float
    effective_sample_size_after: float
    worst_case_clipping_bias_bound: float
    variance_proxy: float
    objective_proxy: float
    support_status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalized(weights: np.ndarray) -> np.ndarray:
    total = float(weights.sum())
    if total <= 0:
        raise ValueError("Importance weights must have positive total")
    return weights / total


def _ess(normalized_weights: np.ndarray) -> float:
    return float(1.0 / np.sum(normalized_weights**2))


class OverlapAwareWeightStabilizer:
    def __init__(
        self, fragile_ess_fraction: float = 0.10, bias_aversion: float = 0.05
    ) -> None:
        if not 0 < fragile_ess_fraction < 1:
            raise ValueError("fragile_ess_fraction must be between zero and one")
        if bias_aversion < 0:
            raise ValueError("bias_aversion must be non-negative")
        self.fragile_ess_fraction = fragile_ess_fraction
        self.bias_aversion = bias_aversion

    def audit(self, weights: Sequence[float]) -> SupportAudit:
        w = np.asarray(weights, dtype=float)
        if w.ndim != 1 or len(w) == 0 or np.any(~np.isfinite(w)) or np.any(w < 0):
            raise ValueError("Weights must be a non-empty finite non-negative vector")
        p = _normalized(w)
        ess = _ess(p)
        count = max(1, int(np.ceil(0.01 * len(w))))
        top_mass = float(np.sort(p)[-count:].sum())
        fraction = ess / len(w)
        status = "SUPPORT_FRAGILE" if fraction < self.fragile_ess_fraction else "SUPPORT_USABLE"
        return SupportAudit(
            observations=len(w),
            effective_sample_size=ess,
            effective_sample_fraction=fraction,
            max_normalized_weight=float(p.max()),
            top_one_percent_weight_mass=top_mass,
            status=status,
        )

    def fit(
        self,
        weights: Sequence[float],
        outcomes: Sequence[float],
        outcome_bounds: tuple[float, float],
        cap_quantiles: Sequence[float] | None = None,
    ) -> StabilizedEstimate:
        w = np.asarray(weights, dtype=float)
        y = np.asarray(outcomes, dtype=float)
        if w.shape != y.shape or w.ndim != 1:
            raise ValueError("Weights and outcomes must be equal-length vectors")
        lower, upper = outcome_bounds
        if lower >= upper or np.any(y < lower) or np.any(y > upper):
            raise ValueError("Outcomes must lie inside declared finite bounds")
        audit = self.audit(w)
        raw_p = _normalized(w)
        raw_estimate = float(raw_p @ y)
        quantiles = (
            np.linspace(0.50, 1.0, 101)
            if cap_quantiles is None
            else np.asarray(cap_quantiles, dtype=float)
        )
        if np.any(quantiles <= 0) or np.any(quantiles > 1):
            raise ValueError("Cap quantiles must lie in (0, 1]")

        best: tuple[float, float, float, float, float, float, float] | None = None
        outcome_range = upper - lower
        for cap in np.unique(np.quantile(w, quantiles)):
            clipped = np.minimum(w, cap)
            p = _normalized(clipped)
            estimate = float(p @ y)
            ess = _ess(p)
            total_variation = 0.5 * float(np.sum(np.abs(raw_p - p)))
            bias_bound = outcome_range * total_variation
            variance_proxy = float(np.sum(p**2 * (y - estimate) ** 2))
            objective = self.bias_aversion * bias_bound**2 + variance_proxy
            row = (
                objective,
                float(cap),
                estimate,
                ess,
                bias_bound,
                variance_proxy,
                float(np.mean(w > cap)),
            )
            if best is None or row[0] < best[0]:
                best = row
        assert best is not None
        objective, cap, estimate, ess_after, bias_bound, variance_proxy, clipped_fraction = best
        return StabilizedEstimate(
            raw_estimate=raw_estimate,
            stabilized_estimate=estimate,
            selected_cap=cap,
            clipped_fraction=clipped_fraction,
            effective_sample_size_before=audit.effective_sample_size,
            effective_sample_size_after=ess_after,
            worst_case_clipping_bias_bound=bias_bound,
            variance_proxy=variance_proxy,
            objective_proxy=objective,
            support_status=audit.status,
        )
