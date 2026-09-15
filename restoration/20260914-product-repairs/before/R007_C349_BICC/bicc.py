"""Bounded-Influence Concentration Certificate (BICC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass(frozen=True)
class CoordinateInfluence:
    coordinate: int
    rms_replacement_effect: float
    mean_absolute_replacement_effect: float
    maximum_observed_replacement_effect: float
    supplied_global_bound: float | None
    observed_bound_violation: bool


@dataclass(frozen=True)
class ConcentrationAudit:
    sample_size: int
    coordinates: int
    output_mean: float
    empirical_output_variance: float
    efron_stein_variance_upper_proxy: float
    supplied_bound_square_sum: float | None
    mcdiarmid_two_sided_radius: float | None
    delta: float
    largest_bound_share: float | None
    effective_coordinates: float | None
    certificate_status: str
    influences: tuple[CoordinateInfluence, ...]

    def mcdiarmid_two_sided_tail_bound(self, deviation: float) -> float | None:
        if self.supplied_bound_square_sum is None:
            return None
        if deviation < 0:
            raise ValueError("deviation must be non-negative")
        if self.supplied_bound_square_sum == 0:
            return 0.0 if deviation > 0 else 1.0
        return min(1.0, 2.0 * np.exp(-2.0 * deviation**2 / self.supplied_bound_square_sum))

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["influences"] = [asdict(item) for item in self.influences]
        return payload


def _evaluate_rows(function: Callable[[np.ndarray], float], samples: np.ndarray) -> np.ndarray:
    values = np.asarray([function(row.copy()) for row in samples], dtype=float)
    if values.shape != (samples.shape[0],) or not np.all(np.isfinite(values)):
        raise ValueError("function must return one finite scalar per sample")
    return values


def audit_concentration(
    function: Callable[[np.ndarray], float],
    base_samples: Sequence[Sequence[float]],
    replacement_samples: Sequence[Sequence[float]],
    *,
    global_coordinate_bounds: Sequence[float] | None = None,
    delta: float = 0.05,
    violation_tolerance: float = 1e-12,
) -> ConcentrationAudit:
    """Audit coordinate replacement influence on a scalar black-box output.

    Rows in ``base_samples`` and ``replacement_samples`` must be independent paired
    draws from the same product-input law. Supplied global bounds are assumptions;
    the audit can falsify them on observed replacements but cannot prove globality.
    """

    base = np.asarray(base_samples, dtype=float)
    replacement = np.asarray(replacement_samples, dtype=float)
    if base.ndim != 2 or base.shape != replacement.shape or base.shape[0] < 2 or base.shape[1] < 1:
        raise ValueError("base and replacement samples must have identical (n>=2, d>=1) shapes")
    if not np.all(np.isfinite(base)) or not np.all(np.isfinite(replacement)):
        raise ValueError("samples must be finite")
    if not 0 < delta < 1:
        raise ValueError("delta must lie strictly between zero and one")

    bounds: np.ndarray | None = None
    if global_coordinate_bounds is not None:
        bounds = np.asarray(global_coordinate_bounds, dtype=float)
        if bounds.shape != (base.shape[1],) or not np.all(np.isfinite(bounds)) or np.any(bounds < 0):
            raise ValueError("global_coordinate_bounds must contain one finite non-negative bound per coordinate")

    output = _evaluate_rows(function, base)
    influence_rows: list[CoordinateInfluence] = []
    squared_effect_total = 0.0
    any_violation = False
    for coordinate in range(base.shape[1]):
        changed = base.copy()
        changed[:, coordinate] = replacement[:, coordinate]
        delta_output = output - _evaluate_rows(function, changed)
        mean_square = float(np.mean(delta_output**2))
        maximum = float(np.max(np.abs(delta_output)))
        supplied = None if bounds is None else float(bounds[coordinate])
        violation = supplied is not None and maximum > supplied + violation_tolerance
        any_violation = any_violation or violation
        squared_effect_total += mean_square
        influence_rows.append(
            CoordinateInfluence(
                coordinate=coordinate,
                rms_replacement_effect=float(np.sqrt(mean_square)),
                mean_absolute_replacement_effect=float(np.mean(np.abs(delta_output))),
                maximum_observed_replacement_effect=maximum,
                supplied_global_bound=supplied,
                observed_bound_violation=violation,
            )
        )

    if bounds is None:
        square_sum = radius = largest_share = effective = None
        status = "EMPIRICAL_INFLUENCE_ONLY"
    else:
        square_sum = float(bounds @ bounds)
        radius = float(np.sqrt(0.5 * square_sum * np.log(2.0 / delta)))
        if square_sum == 0:
            largest_share, effective = 0.0, float(base.shape[1])
        else:
            shares = bounds**2 / square_sum
            largest_share = float(np.max(shares))
            effective = float(1.0 / np.sum(shares**2))
        status = "OBSERVED_BOUND_VIOLATION" if any_violation else "ASSUMPTION_CONDITIONAL_CERTIFICATE"

    return ConcentrationAudit(
        sample_size=base.shape[0],
        coordinates=base.shape[1],
        output_mean=float(np.mean(output)),
        empirical_output_variance=float(np.var(output, ddof=1)),
        efron_stein_variance_upper_proxy=0.5 * squared_effect_total,
        supplied_bound_square_sum=square_sum,
        mcdiarmid_two_sided_radius=radius,
        delta=delta,
        largest_bound_share=largest_share,
        effective_coordinates=effective,
        certificate_status=status,
        influences=tuple(influence_rows),
    )
