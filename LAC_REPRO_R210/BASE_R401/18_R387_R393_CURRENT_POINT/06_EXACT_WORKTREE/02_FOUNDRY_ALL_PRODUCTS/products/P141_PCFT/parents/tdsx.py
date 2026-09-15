"""Tipping-Distance and Sensitivity-surface Explorer (TDSX) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
from typing import Callable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class TippingPoint:
    parameters: dict[str, float]
    metric: float
    normalized_euclidean_distance: float
    normalized_manhattan_distance: float


@dataclass(frozen=True)
class SensitivitySurface:
    parameter_names: tuple[str, ...]
    grid_shape: tuple[int, ...]
    evaluated_points: int
    baseline_parameters: dict[str, float]
    baseline_metric: float
    decision_threshold: float
    baseline_decision: bool
    robust_surface_share: float
    tipping_point: TippingPoint | None
    one_way_tipping_values: dict[str, float | None]
    metric_minimum: float
    metric_maximum: float
    status: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["tipping_point"] = None if self.tipping_point is None else asdict(self.tipping_point)
        return payload


def confounding_e_value(risk_ratio: float) -> float:
    """Minimum equal-strength confounder associations needed to explain a risk ratio."""
    if not np.isfinite(risk_ratio) or risk_ratio <= 0:
        raise ValueError("risk_ratio must be finite and positive")
    harmful = risk_ratio if risk_ratio >= 1 else 1.0 / risk_ratio
    return float(harmful + np.sqrt(harmful * (harmful - 1.0)))


def missing_mean_tipping_value(
    observed_values: Sequence[float], missing_count: int, decision_threshold: float
) -> float | None:
    """Common imputed missing value at which the completed-data mean hits a threshold."""
    observed = np.asarray(observed_values, dtype=float)
    if observed.ndim != 1 or observed.size == 0 or not np.all(np.isfinite(observed)):
        raise ValueError("observed_values must be a non-empty finite vector")
    if not isinstance(missing_count, int) or missing_count < 0 or not np.isfinite(decision_threshold):
        raise ValueError("missing_count must be non-negative integer and threshold finite")
    if missing_count == 0:
        return None
    total = observed.size + missing_count
    return float((decision_threshold * total - np.sum(observed)) / missing_count)


def explore_sensitivity_surface(
    evaluator: Callable[[Mapping[str, float]], float],
    parameter_grids: Mapping[str, Sequence[float]],
    baseline_parameters: Mapping[str, float],
    *,
    decision_threshold: float,
    decision_direction: str = "ABOVE",
    maximum_points: int = 200_000,
) -> SensitivitySurface:
    """Evaluate a black-box metric over a declared parameter surface and find the nearest decision flip."""

    if not parameter_grids or set(parameter_grids) != set(baseline_parameters):
        raise ValueError("parameter grids and baseline parameters must have the same non-empty names")
    if decision_direction not in ("ABOVE", "BELOW") or not np.isfinite(decision_threshold):
        raise ValueError("direction must be ABOVE/BELOW and threshold finite")
    names = tuple(parameter_grids)
    grids: list[np.ndarray] = []
    ranges = []
    for name in names:
        values = np.unique(np.asarray(parameter_grids[name], dtype=float))
        baseline = baseline_parameters[name]
        if values.ndim != 1 or values.size < 2 or not np.all(np.isfinite(values)) or not np.isfinite(baseline):
            raise ValueError("each parameter grid needs at least two finite values and a finite baseline")
        if baseline < values[0] or baseline > values[-1]:
            raise ValueError("baseline parameters must lie inside their grids")
        grids.append(values)
        ranges.append(float(values[-1] - values[0]))
    point_count = int(np.prod([values.size for values in grids]))
    if point_count > maximum_points:
        raise ValueError("sensitivity surface exceeds maximum_points")

    def decision(metric: float) -> bool:
        return metric >= decision_threshold if decision_direction == "ABOVE" else metric <= decision_threshold

    baseline_dict = {name: float(baseline_parameters[name]) for name in names}
    baseline_metric = float(evaluator(baseline_dict))
    if not np.isfinite(baseline_metric):
        raise ValueError("evaluator must return finite scalar metrics")
    baseline_decision = decision(baseline_metric)
    rows = []
    metrics = []
    decisions = []
    for values in product(*grids):
        params = {name: float(value) for name, value in zip(names, values)}
        metric = float(evaluator(params))
        if not np.isfinite(metric):
            raise ValueError("evaluator returned a non-finite metric")
        rows.append(params); metrics.append(metric); decisions.append(decision(metric))
    metrics_array = np.asarray(metrics)
    same = np.asarray(decisions) == baseline_decision
    opposite_indices = np.where(~same)[0]
    tipping = None
    if opposite_indices.size:
        distances = []
        manhattan = []
        for index in opposite_indices:
            normalized = np.asarray([
                (rows[index][name] - baseline_dict[name]) / parameter_range
                for name, parameter_range in zip(names, ranges)
            ])
            distances.append(float(np.linalg.norm(normalized)))
            manhattan.append(float(np.sum(np.abs(normalized))))
        local = int(np.argmin(distances))
        index = int(opposite_indices[local])
        tipping = TippingPoint(rows[index], float(metrics_array[index]), distances[local], manhattan[local])

    one_way: dict[str, float | None] = {}
    for name, values in zip(names, grids):
        candidates = []
        for value in values:
            params = dict(baseline_dict); params[name] = float(value)
            metric = float(evaluator(params))
            if decision(metric) != baseline_decision:
                candidates.append(float(value))
        one_way[name] = min(candidates, key=lambda value: abs(value - baseline_dict[name])) if candidates else None
    return SensitivitySurface(
        names, tuple(values.size for values in grids), point_count, baseline_dict, baseline_metric,
        float(decision_threshold), baseline_decision, float(np.mean(same)), tipping, one_way,
        float(np.min(metrics_array)), float(np.max(metrics_array)),
        "TIPPING_POINT_FOUND" if tipping is not None else "NO_FLIP_INSIDE_DECLARED_SURFACE",
    )
