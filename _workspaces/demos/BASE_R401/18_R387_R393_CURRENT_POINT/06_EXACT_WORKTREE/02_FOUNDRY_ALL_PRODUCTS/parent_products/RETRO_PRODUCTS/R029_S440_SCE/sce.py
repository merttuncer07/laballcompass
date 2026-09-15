"""Specification Curve Engine (SCE) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class SpecificationResult:
    outcome: str
    treatment: str
    control_set: str
    sample: str
    n: int
    parameters: int
    rank: int
    condition_number: float
    estimate: float | None
    robust_standard_error: float | None
    confidence_low: float | None
    confidence_high: float | None
    status: str


@dataclass(frozen=True)
class SpecificationCurve:
    results: tuple[SpecificationResult, ...]
    valid_specifications: int
    invalid_specifications: int
    estimate_minimum: float | None
    estimate_median: float | None
    estimate_maximum: float | None
    positive_share: float | None
    negative_share: float | None
    significantly_positive_share: float | None
    significantly_negative_share: float | None
    sign_stable: bool | None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["results"] = [asdict(item) for item in self.results]
        return payload


def _as_vector(name: str, values: Sequence[float], n: int | None = None) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.ndim != 1 or (n is not None and vector.shape != (n,)):
        raise ValueError(f"{name} must be a one-dimensional vector of the common length")
    return vector


def run_specification_curve(
    *,
    outcomes: Mapping[str, Sequence[float]],
    treatments: Mapping[str, Sequence[float]],
    controls: Mapping[str, Sequence[float]],
    control_sets: Mapping[str, Sequence[str]],
    samples: Mapping[str, Sequence[bool]],
    confidence_z: float = 1.96,
) -> SpecificationCurve:
    """Run every declared outcome × treatment × control-set × sample OLS specification."""

    if not outcomes or not treatments or not control_sets or not samples:
        raise ValueError("outcomes, treatments, control_sets, and samples cannot be empty")
    first = next(iter(outcomes.values()))
    n = len(first)
    if n < 3 or confidence_z <= 0 or not np.isfinite(confidence_z):
        raise ValueError("common data length must be at least three and confidence_z positive")
    y_map = {name: _as_vector(f"outcome {name}", values, n) for name, values in outcomes.items()}
    t_map = {name: _as_vector(f"treatment {name}", values, n) for name, values in treatments.items()}
    c_map = {name: _as_vector(f"control {name}", values, n) for name, values in controls.items()}
    sample_map = {name: np.asarray(values, dtype=bool) for name, values in samples.items()}
    if any(mask.shape != (n,) for mask in sample_map.values()):
        raise ValueError("every sample mask must have the common length")
    for set_name, names in control_sets.items():
        missing = [name for name in names if name not in c_map]
        if missing:
            raise ValueError(f"control set {set_name} references missing controls: {missing}")

    results: list[SpecificationResult] = []
    for y_name, t_name, controls_name, sample_name in product(
        y_map, t_map, control_sets, sample_map
    ):
        y = y_map[y_name]
        treatment = t_map[t_name]
        control_names = tuple(control_sets[controls_name])
        columns = [np.ones(n), treatment] + [c_map[name] for name in control_names]
        full_x = np.column_stack(columns)
        mask = sample_map[sample_name] & np.isfinite(y) & np.all(np.isfinite(full_x), axis=1)
        yy, x = y[mask], full_x[mask]
        rows, parameters = x.shape
        rank = int(np.linalg.matrix_rank(x)) if rows else 0
        condition = float(np.linalg.cond(x)) if rows else float("inf")
        if rows <= parameters or rank < parameters:
            results.append(
                SpecificationResult(
                    y_name, t_name, controls_name, sample_name, rows, parameters, rank, condition,
                    None, None, None, None, "INSUFFICIENT_OR_RANK_DEFICIENT",
                )
            )
            continue

        beta = np.linalg.lstsq(x, yy, rcond=None)[0]
        residual = yy - x @ beta
        bread = np.linalg.inv(x.T @ x)
        meat = x.T @ (x * residual[:, None] ** 2)
        covariance = (rows / (rows - parameters)) * bread @ meat @ bread
        standard_error = float(np.sqrt(max(covariance[1, 1], 0.0)))
        estimate = float(beta[1])
        results.append(
            SpecificationResult(
                y_name,
                t_name,
                controls_name,
                sample_name,
                rows,
                parameters,
                rank,
                condition,
                estimate,
                standard_error,
                estimate - confidence_z * standard_error,
                estimate + confidence_z * standard_error,
                "OK",
            )
        )

    valid = [item for item in results if item.status == "OK"]
    if not valid:
        summary = (None,) * 7 + (None,)
        minimum = median = maximum = positive = negative = sig_positive = sig_negative = sign_stable = None
    else:
        estimates = np.asarray([item.estimate for item in valid], dtype=float)
        minimum, median, maximum = map(float, [np.min(estimates), np.median(estimates), np.max(estimates)])
        positive = float(np.mean(estimates > 0))
        negative = float(np.mean(estimates < 0))
        sig_positive = float(np.mean([item.confidence_low > 0 for item in valid]))
        sig_negative = float(np.mean([item.confidence_high < 0 for item in valid]))
        sign_stable = bool(np.all(estimates >= 0) or np.all(estimates <= 0))
    return SpecificationCurve(
        tuple(results), len(valid), len(results) - len(valid), minimum, median, maximum,
        positive, negative, sig_positive, sig_negative, sign_stable,
    )
