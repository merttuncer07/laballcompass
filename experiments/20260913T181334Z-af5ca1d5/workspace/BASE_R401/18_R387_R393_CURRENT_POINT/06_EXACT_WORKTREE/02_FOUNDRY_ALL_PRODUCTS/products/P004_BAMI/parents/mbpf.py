"""Mortgage Burnout-adjusted Prepayment Forecaster (MBPF) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class BurnoutForecast:
    months: tuple[int, ...]
    active_loans: tuple[float, ...]
    monthly_prepayments: tuple[float, ...]
    monthly_defaults: tuple[float, ...]
    effective_prepayment_rates: tuple[float, ...]
    surviving_average_propensity: tuple[float, ...]
    frailty_class_survivors: tuple[tuple[float, ...], ...]
    cumulative_prepayments: float
    cumulative_defaults: float
    naive_homogeneous_cumulative_prepayments: float
    naive_overprediction_fraction: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def forecast_burnout_prepayment(
    *,
    cohort_size: int,
    base_monthly_prepayment_rates: Sequence[float],
    propensity_multipliers: Sequence[float],
    initial_class_weights: Sequence[float],
    monthly_default_rates: Sequence[float] | float = 0.0,
) -> BurnoutForecast:
    """Forecast prepayment while high-propensity classes selectively leave the pool."""

    base = np.asarray(base_monthly_prepayment_rates, dtype=float)
    multipliers = np.asarray(propensity_multipliers, dtype=float)
    weights = np.asarray(initial_class_weights, dtype=float)
    if not isinstance(cohort_size, int) or cohort_size <= 0:
        raise ValueError("cohort_size must be a positive integer")
    if base.ndim != 1 or base.size < 1 or np.any(base < 0) or not np.all(np.isfinite(base)):
        raise ValueError("base_monthly_prepayment_rates must be finite and nonnegative")
    if multipliers.ndim != 1 or weights.shape != multipliers.shape or multipliers.size < 1 or np.any(multipliers < 0) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("propensity multipliers and weights must be matching nonnegative vectors")
    weights = weights / weights.sum()
    defaults = np.asarray(monthly_default_rates, dtype=float)
    if defaults.ndim == 0:
        defaults = np.full(base.size, float(defaults))
    if defaults.shape != base.shape or np.any(defaults < 0) or not np.all(np.isfinite(defaults)):
        raise ValueError("monthly_default_rates must be a nonnegative scalar or horizon vector")
    class_rates = base[:, None] * multipliers[None, :]
    if np.any(class_rates + defaults[:, None] > 1 + 1e-12):
        raise ValueError("a class prepayment plus default rate exceeds one")

    survivors = cohort_size * weights
    active_history = [float(survivors.sum())]
    class_history = [tuple(map(float, survivors))]
    average_history = [float(np.dot(survivors, multipliers) / survivors.sum())]
    prepayments: list[float] = []
    default_counts: list[float] = []
    effective_rates: list[float] = []
    for month in range(base.size):
        active = float(survivors.sum())
        prepaid_by_class = survivors * class_rates[month]
        defaulted_by_class = survivors * defaults[month]
        prepaid = float(prepaid_by_class.sum())
        defaulted = float(defaulted_by_class.sum())
        prepayments.append(prepaid)
        default_counts.append(defaulted)
        effective_rates.append(0.0 if active <= 0 else prepaid / active)
        survivors = survivors - prepaid_by_class - defaulted_by_class
        active_history.append(float(survivors.sum()))
        class_history.append(tuple(map(float, survivors)))
        average_history.append(0.0 if survivors.sum() <= 0 else float(np.dot(survivors, multipliers) / survivors.sum()))

    mean_multiplier = float(np.dot(weights, multipliers))
    naive_active = float(cohort_size)
    naive_prepay = 0.0
    for month in range(base.size):
        monthly_prepay = naive_active * base[month] * mean_multiplier
        monthly_default = naive_active * defaults[month]
        naive_prepay += monthly_prepay
        naive_active -= monthly_prepay + monthly_default
    actual = float(sum(prepayments))
    overprediction = 0.0 if actual <= 0 else float(naive_prepay / actual - 1.0)
    return BurnoutForecast(
        months=tuple(range(base.size + 1)),
        active_loans=tuple(active_history),
        monthly_prepayments=tuple(prepayments),
        monthly_defaults=tuple(default_counts),
        effective_prepayment_rates=tuple(effective_rates),
        surviving_average_propensity=tuple(average_history),
        frailty_class_survivors=tuple(class_history),
        cumulative_prepayments=actual,
        cumulative_defaults=float(sum(default_counts)),
        naive_homogeneous_cumulative_prepayments=float(naive_prepay),
        naive_overprediction_fraction=overprediction,
        status="BURNOUT_SELECTION_FORECAST_READY",
    )
