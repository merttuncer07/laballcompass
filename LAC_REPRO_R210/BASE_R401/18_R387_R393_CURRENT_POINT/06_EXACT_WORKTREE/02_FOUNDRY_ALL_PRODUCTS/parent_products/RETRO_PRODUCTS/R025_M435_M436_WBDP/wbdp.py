"""Wasserstein Barycenter and Displacement Planner (WBDP) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class Distribution:
    name: str
    positions: tuple[float, ...]
    masses: tuple[float, ...]


@dataclass(frozen=True)
class DistributionPlan:
    name: str
    positions: tuple[float, ...]
    masses: tuple[float, ...]
    mean: float
    variance: float
    source_wasserstein_distances: dict[str, float]
    weighted_squared_transport_objective: float
    path_fraction: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def _validate(distribution: Distribution) -> tuple[np.ndarray, np.ndarray]:
    x, m = np.asarray(distribution.positions, dtype=float), np.asarray(distribution.masses, dtype=float)
    if not distribution.name or x.ndim != 1 or m.shape != x.shape or x.size == 0:
        raise ValueError("distribution needs a name and equally sized non-empty position/mass vectors")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(m)) or np.any(m < 0) or np.sum(m) <= 0:
        raise ValueError("positions must be finite and masses finite/non-negative with positive total")
    order = np.argsort(x, kind="stable"); x, m = x[order], m[order] / np.sum(m)
    unique, inverse = np.unique(x, return_inverse=True); combined = np.zeros(unique.size)
    np.add.at(combined, inverse, m)
    return unique, combined


def _segments(distributions: Sequence[Distribution]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    parsed = [_validate(item) for item in distributions]
    breakpoints = {0.0, 1.0}
    for _, masses in parsed:
        breakpoints.update(map(float, np.cumsum(masses)[:-1]))
    edges = np.asarray(sorted(breakpoints)); segment_masses = np.diff(edges); midpoint = (edges[:-1] + edges[1:]) / 2
    quantiles = []
    for positions, masses in parsed:
        indices = np.searchsorted(np.cumsum(masses), midpoint, side="right")
        quantiles.append(positions[indices])
    return segment_masses, np.asarray(quantiles), edges


def _compress(positions: np.ndarray, masses: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    unique, inverse = np.unique(positions, return_inverse=True); combined = np.zeros(unique.size)
    np.add.at(combined, inverse, masses)
    return unique, combined


def wasserstein_distance(first: Distribution, second: Distribution) -> float:
    masses, quantiles, _ = _segments([first, second])
    return float(np.sqrt(np.sum(masses * (quantiles[0] - quantiles[1]) ** 2)))


def wasserstein_barycenter(
    distributions: Sequence[Distribution], weights: Sequence[float] | None = None
) -> DistributionPlan:
    records = tuple(distributions)
    if not records:
        raise ValueError("at least one distribution is required")
    if len({item.name for item in records}) != len(records):
        raise ValueError("distribution names must be unique")
    w = np.ones(len(records)) / len(records) if weights is None else np.asarray(weights, dtype=float)
    if w.shape != (len(records),) or not np.all(np.isfinite(w)) or np.any(w < 0) or np.sum(w) <= 0:
        raise ValueError("weights must be finite non-negative and match distributions")
    w = w / np.sum(w)
    segment_masses, quantiles, _ = _segments(records)
    bary_quantile = w @ quantiles
    positions, masses = _compress(bary_quantile, segment_masses)
    bary = Distribution("BARYCENTER", tuple(map(float, positions)), tuple(map(float, masses)))
    distances = {item.name: wasserstein_distance(item, bary) for item in records}
    mean = float(positions @ masses); variance = float(((positions - mean) ** 2) @ masses)
    objective = float(sum(weight * distances[item.name] ** 2 for weight, item in zip(w, records)))
    return DistributionPlan(bary.name, bary.positions, bary.masses, mean, variance, distances, objective, None)


def displacement_interpolation(source: Distribution, target: Distribution, fraction: float) -> DistributionPlan:
    if source.name == target.name:
        raise ValueError("source and target names must differ")
    if not np.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError("fraction must lie in [0,1]")
    segment_masses, quantiles, _ = _segments([source, target])
    interpolated = (1 - fraction) * quantiles[0] + fraction * quantiles[1]
    positions, masses = _compress(interpolated, segment_masses)
    result = Distribution(f"INTERPOLATION_{fraction:g}", tuple(map(float, positions)), tuple(map(float, masses)))
    distances = {source.name: wasserstein_distance(source, result), target.name: wasserstein_distance(target, result)}
    mean = float(positions @ masses); variance = float(((positions - mean) ** 2) @ masses)
    return DistributionPlan(result.name, result.positions, result.masses, mean, variance, distances,
                            float(distances[source.name] ** 2 + distances[target.name] ** 2), float(fraction))
