from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    name: str
    capacity: float
    lead_time: float = 0.0
    yield_fraction: float = 1.0


@dataclass(frozen=True)
class DeployabilityTippingResult:
    baseline_deployable: float
    target: float
    tipping_edge: str | None
    tipping_capacity: float | None
    tipping_deployable: float | None
    status: str


def deployable_on_series_path(active_stock: float, edges: list[Edge], horizon: float) -> float:
    if active_stock < 0 or horizon < 0:
        raise ValueError("stock and horizon must be nonnegative")
    if sum(edge.lead_time for edge in edges) > horizon:
        return 0.0
    amount = active_stock
    for edge in edges:
        if not 0 <= edge.yield_fraction <= 1 or edge.capacity < 0:
            raise ValueError("invalid edge")
        amount = min(amount, edge.capacity) * edge.yield_fraction
    return amount


def explore_deployable_tipping(
    active_stock: float,
    edges: list[Edge],
    *,
    horizon: float,
    target: float,
    capacity_grid: dict[str, list[float]],
) -> DeployabilityTippingResult:
    baseline = deployable_on_series_path(active_stock, edges, horizon)
    candidates: list[tuple[float, str, float, float]] = []
    by_name = {edge.name: edge for edge in edges}
    for name, grid in capacity_grid.items():
        if name not in by_name:
            raise KeyError(name)
        base_edge = by_name[name]
        for value in grid:
            changed = [Edge(e.name, value if e.name == name else e.capacity, e.lead_time, e.yield_fraction) for e in edges]
            delivered = deployable_on_series_path(active_stock, changed, horizon)
            if delivered >= target:
                candidates.append((abs(value - base_edge.capacity), name, value, delivered))
    if not candidates:
        return DeployabilityTippingResult(baseline, target, None, None, None, "NO_TIPPING_POINT_ON_GRID")
    _, name, value, delivered = min(candidates)
    return DeployabilityTippingResult(baseline, target, name, value, delivered, "DEPLOYABLE_TARGET_TIPPING_POINT_FOUND")
