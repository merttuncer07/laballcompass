"""Preferential-Channel Breakthrough Estimator (PCBE) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import heapq
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class BreakthroughResult:
    spanning: bool
    widest_path_bottleneck: float
    widest_path: tuple[tuple[int, int], ...]
    path_tortuosity: float
    effective_conductance: float
    baseline_effective_conductance: float | None
    conductance_jump_ratio: float | None
    channel_threshold: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _widest_path(field: np.ndarray) -> tuple[float, tuple[tuple[int, int], ...]]:
    rows, columns = field.shape
    best = np.full(field.shape, -np.inf)
    parent: dict[tuple[int, int], tuple[int, int] | None] = {}
    heap: list[tuple[float, int, int]] = []
    for row in range(rows):
        best[row, 0] = field[row, 0]
        parent[(row, 0)] = None
        heapq.heappush(heap, (-float(field[row, 0]), row, 0))
    target = None
    while heap:
        negative_score, row, column = heapq.heappop(heap)
        score = -negative_score
        if score < best[row, column] - 1e-15:
            continue
        if column == columns - 1:
            target = (row, column); break
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = row + dr, column + dc
            if 0 <= rr < rows and 0 <= cc < columns:
                candidate = min(score, float(field[rr, cc]))
                if candidate > best[rr, cc]:
                    best[rr, cc] = candidate
                    parent[(rr, cc)] = (row, column)
                    heapq.heappush(heap, (-candidate, rr, cc))
    if target is None:
        raise RuntimeError("grid unexpectedly has no left-to-right path")
    path = []
    node = target
    while node is not None:
        path.append(node); node = parent[node]
    path.reverse()
    return float(best[target]), tuple(path)


def _edge_conductance(a: float, b: float) -> float:
    return 2.0 * a * b / (a + b)


def _effective_conductance(field: np.ndarray) -> float:
    rows, columns = field.shape
    if columns == 2:
        return float(sum(_edge_conductance(field[r, 0], field[r, 1]) for r in range(rows)))
    unknown = [(r, c) for r in range(rows) for c in range(1, columns - 1)]
    index = {node: i for i, node in enumerate(unknown)}
    matrix = np.zeros((len(unknown), len(unknown)))
    rhs = np.zeros(len(unknown))
    for node, i in index.items():
        r, c = node
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < rows and 0 <= cc < columns):
                continue
            conductance = _edge_conductance(field[r, c], field[rr, cc])
            matrix[i, i] += conductance
            if cc == 0:
                rhs[i] += conductance
            elif cc != columns - 1:
                matrix[i, index[(rr, cc)]] -= conductance
    pressures = np.linalg.solve(matrix, rhs)
    total_flux = 0.0
    for r in range(rows):
        conductance = _edge_conductance(field[r, 0], field[r, 1])
        total_flux += conductance * (1.0 - pressures[index[(r, 1)]])
    return float(total_flux)


def estimate_channel_breakthrough(
    conductance_field: Sequence[Sequence[float]],
    *,
    channel_threshold: float,
    baseline_conductance_field: Sequence[Sequence[float]] | None = None,
    minimum_system_jump_ratio: float = 2.0,
) -> BreakthroughResult:
    """Require both a spanning high-conductance path and a system-level conductance jump."""

    field = np.asarray(conductance_field, dtype=float)
    if field.ndim != 2 or min(field.shape) < 2 or np.any(field <= 0) or not np.all(np.isfinite(field)):
        raise ValueError("conductance_field must be a finite positive 2D grid")
    if channel_threshold <= 0 or minimum_system_jump_ratio <= 0:
        raise ValueError("thresholds must be positive")
    baseline = None
    if baseline_conductance_field is not None:
        baseline = np.asarray(baseline_conductance_field, dtype=float)
        if baseline.shape != field.shape or np.any(baseline <= 0) or not np.all(np.isfinite(baseline)):
            raise ValueError("baseline field must be positive and match the current grid")
    bottleneck, path = _widest_path(field)
    spanning = bottleneck >= channel_threshold
    effective = _effective_conductance(field)
    baseline_effective = None if baseline is None else _effective_conductance(baseline)
    jump = None if baseline_effective is None else effective / baseline_effective
    tortuosity = (len(path) - 1) / (field.shape[1] - 1)
    if spanning and (jump is None or jump >= minimum_system_jump_ratio):
        status = "SPANNING_CHANNEL_BREAKTHROUGH_DETECTED"
    elif spanning:
        status = "CHANNEL_SPANS_WITHOUT_REQUIRED_SYSTEM_JUMP"
    else:
        status = "PREFERENTIAL_CHANNEL_NOT_YET_SPANNING"
    return BreakthroughResult(
        spanning=spanning,
        widest_path_bottleneck=bottleneck,
        widest_path=path,
        path_tortuosity=float(tortuosity),
        effective_conductance=effective,
        baseline_effective_conductance=baseline_effective,
        conductance_jump_ratio=None if jump is None else float(jump),
        channel_threshold=float(channel_threshold),
        status=status,
    )
