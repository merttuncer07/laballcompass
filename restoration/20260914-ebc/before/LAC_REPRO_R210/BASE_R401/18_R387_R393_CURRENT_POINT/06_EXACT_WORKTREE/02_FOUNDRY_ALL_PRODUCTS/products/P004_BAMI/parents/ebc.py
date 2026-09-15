"""Evidence Borrowing Controller (EBC) v0.1 for normal estimates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class HistoricalEstimate:
    name: str
    estimate: float
    standard_error: float
    maximum_power: float = 1.0


@dataclass(frozen=True)
class BorrowingContribution:
    name: str
    estimate: float
    standard_error: float
    conflict_z: float
    commensurability_factor: float
    pre_cap_power: float
    final_power: float
    borrowed_precision: float


@dataclass(frozen=True)
class BorrowingResult:
    current_estimate: float
    current_standard_error: float
    posterior_estimate: float
    posterior_standard_error: float
    confidence_low: float
    confidence_high: float
    current_precision: float
    borrowed_precision: float
    borrowing_precision_ratio: float
    cap_scale: float
    current_information_share: float
    contributions: tuple[BorrowingContribution, ...]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["contributions"] = [asdict(item) for item in self.contributions]
        return payload


def borrow_evidence(
    current_estimate: float,
    current_standard_error: float,
    historical: Sequence[HistoricalEstimate],
    *,
    compatibility_scale: float = 1.5,
    borrowing_cap_ratio: float = 2.0,
    confidence_z: float = 1.96,
) -> BorrowingResult:
    """Combine current and historical normal estimates with conflict-adaptive power weights."""

    numbers = [current_estimate, current_standard_error, compatibility_scale, borrowing_cap_ratio, confidence_z]
    if not all(np.isfinite(numbers)) or current_standard_error <= 0 or compatibility_scale <= 0:
        raise ValueError("current SE and compatibility scale must be positive; all inputs finite")
    if borrowing_cap_ratio < 0 or confidence_z <= 0:
        raise ValueError("borrowing cap must be non-negative and confidence_z positive")
    records = tuple(historical)
    if len({record.name for record in records}) != len(records):
        raise ValueError("historical estimate names must be unique")
    for record in records:
        if (
            not record.name
            or not np.isfinite(record.estimate)
            or not np.isfinite(record.standard_error)
            or not np.isfinite(record.maximum_power)
            or record.standard_error <= 0
            or not 0 <= record.maximum_power <= 1
        ):
            raise ValueError("historical estimates require finite values, positive SE, and power in [0,1]")

    current_precision = 1.0 / current_standard_error**2
    provisional: list[tuple[HistoricalEstimate, float, float, float]] = []
    pre_cap_precision = 0.0
    for record in records:
        conflict_z = abs(record.estimate - current_estimate) / np.sqrt(
            record.standard_error**2 + current_standard_error**2
        )
        compatibility = float(np.exp(-0.5 * (conflict_z / compatibility_scale) ** 2))
        pre_cap_power = record.maximum_power * compatibility
        precision = pre_cap_power / record.standard_error**2
        provisional.append((record, conflict_z, compatibility, pre_cap_power))
        pre_cap_precision += precision

    allowed_precision = borrowing_cap_ratio * current_precision
    cap_scale = 1.0 if pre_cap_precision == 0 else min(1.0, allowed_precision / pre_cap_precision)
    contributions: list[BorrowingContribution] = []
    weighted_numerator = current_precision * current_estimate
    borrowed_precision = 0.0
    for record, conflict_z, compatibility, pre_cap_power in provisional:
        final_power = pre_cap_power * cap_scale
        precision = final_power / record.standard_error**2
        borrowed_precision += precision
        weighted_numerator += precision * record.estimate
        contributions.append(
            BorrowingContribution(
                record.name, record.estimate, record.standard_error, float(conflict_z), compatibility,
                float(pre_cap_power), float(final_power), float(precision),
            )
        )

    total_precision = current_precision + borrowed_precision
    posterior = weighted_numerator / total_precision
    posterior_se = float(1.0 / np.sqrt(total_precision))
    return BorrowingResult(
        current_estimate=float(current_estimate),
        current_standard_error=float(current_standard_error),
        posterior_estimate=float(posterior),
        posterior_standard_error=posterior_se,
        confidence_low=float(posterior - confidence_z * posterior_se),
        confidence_high=float(posterior + confidence_z * posterior_se),
        current_precision=float(current_precision),
        borrowed_precision=float(borrowed_precision),
        borrowing_precision_ratio=float(borrowed_precision / current_precision),
        cap_scale=float(cap_scale),
        current_information_share=float(current_precision / total_precision),
        contributions=tuple(contributions),
    )
