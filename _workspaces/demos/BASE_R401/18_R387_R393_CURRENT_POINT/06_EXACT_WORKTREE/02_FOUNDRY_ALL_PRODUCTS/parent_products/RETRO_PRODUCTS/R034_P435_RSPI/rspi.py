"""Remote Synchronization Pathway Identifier (RSPI) v0.1."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class RemotePair:
    endpoint_a: str
    endpoint_b: str
    endpoint_phase_locking: float
    graph_path: tuple[str, ...]
    mediator_phase_locking_to_a: tuple[float, ...]
    mediator_phase_locking_to_b: tuple[float, ...]
    weakest_mediator_decoupling_margin: float


@dataclass(frozen=True)
class RemoteSynchronizationResult:
    node_names: tuple[str, ...]
    phase_locking_matrix: tuple[tuple[float, ...], ...]
    remote_pairs: tuple[RemotePair, ...]
    synchronized_nonadjacent_pair_count: int
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _shortest_path(adjacency: np.ndarray, source: int, target: int) -> tuple[int, ...] | None:
    parent = {source: None}; queue = deque([source])
    while queue:
        node = queue.popleft()
        if node == target:
            path = []
            while node is not None:
                path.append(node); node = parent[node]
            return tuple(reversed(path))
        for neighbor in np.flatnonzero(adjacency[node]):
            neighbor = int(neighbor)
            if neighbor not in parent:
                parent[neighbor] = node; queue.append(neighbor)
    return None


def identify_remote_synchronization(
    phases: Sequence[Sequence[float]],
    adjacency_matrix: Sequence[Sequence[bool]],
    *,
    node_names: Sequence[str] | None = None,
    endpoint_phase_locking_threshold: float = 0.85,
    mediator_phase_locking_ceiling: float = 0.45,
) -> RemoteSynchronizationResult:
    """Find synchronized non-neighbors whose shortest-path mediators remain unsynchronized."""

    phase = np.asarray(phases, dtype=float)
    adjacency = np.asarray(adjacency_matrix, dtype=bool)
    if phase.ndim != 2 or phase.shape[0] < 10 or phase.shape[1] < 3 or not np.all(np.isfinite(phase)):
        raise ValueError("phases must be a finite time-by-node matrix with >=10 samples and >=3 nodes")
    n = phase.shape[1]
    if adjacency.shape != (n, n) or not np.array_equal(adjacency, adjacency.T) or np.any(np.diag(adjacency)):
        raise ValueError("adjacency must be symmetric, square, and have a zero diagonal")
    if not 0 <= mediator_phase_locking_ceiling < endpoint_phase_locking_threshold <= 1:
        raise ValueError("phase-locking thresholds are inconsistent")
    names = tuple(node_names) if node_names is not None else tuple(f"node_{i}" for i in range(n))
    if len(names) != n or len(set(names)) != n:
        raise ValueError("node_names must be unique and match phase columns")

    plv = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            value = float(abs(np.mean(np.exp(1j * (phase[:, i] - phase[:, j])))))
            plv[i, j] = plv[j, i] = value
    remote: list[RemotePair] = []; synchronized_nonadjacent = 0
    for i in range(n):
        for j in range(i + 1, n):
            if adjacency[i, j] or plv[i, j] < endpoint_phase_locking_threshold:
                continue
            synchronized_nonadjacent += 1
            path = _shortest_path(adjacency, i, j)
            if path is None or len(path) < 3:
                continue
            mediators = path[1:-1]
            to_a = tuple(float(plv[i, m]) for m in mediators)
            to_b = tuple(float(plv[j, m]) for m in mediators)
            worst = max(to_a + to_b)
            if worst <= mediator_phase_locking_ceiling:
                remote.append(RemotePair(
                    endpoint_a=str(names[i]), endpoint_b=str(names[j]),
                    endpoint_phase_locking=float(plv[i, j]),
                    graph_path=tuple(str(names[k]) for k in path),
                    mediator_phase_locking_to_a=to_a,
                    mediator_phase_locking_to_b=to_b,
                    weakest_mediator_decoupling_margin=float(mediator_phase_locking_ceiling - worst),
                ))
    remote.sort(key=lambda pair: pair.endpoint_phase_locking, reverse=True)
    return RemoteSynchronizationResult(
        node_names=tuple(map(str, names)),
        phase_locking_matrix=tuple(tuple(map(float, row)) for row in plv),
        remote_pairs=tuple(remote),
        synchronized_nonadjacent_pair_count=synchronized_nonadjacent,
        status="REMOTE_SYNCHRONIZATION_PATHWAY_FOUND" if remote else "NO_REMOTE_SYNCHRONIZATION_PATHWAY_FOUND",
    )
