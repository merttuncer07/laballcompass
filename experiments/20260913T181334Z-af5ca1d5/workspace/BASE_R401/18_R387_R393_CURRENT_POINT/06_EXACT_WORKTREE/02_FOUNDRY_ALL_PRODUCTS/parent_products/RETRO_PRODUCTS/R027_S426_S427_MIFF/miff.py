"""Modular Inference Flow Firewall (MIFF) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections import deque
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class InformationFlow:
    source: str
    target: str
    gain: float
    cut_cost: float = 1.0
    label: str = ""


@dataclass(frozen=True)
class FirewallResult:
    modules: tuple[str, ...]
    suspect_sources: tuple[str, ...]
    protected_targets: tuple[str, ...]
    exposed_paths: tuple[tuple[str, ...], ...]
    cut_edges: tuple[InformationFlow, ...]
    total_cut_cost: float
    full_loop_spectral_radius: float
    firewalled_loop_spectral_radius: float
    full_protected_contamination: tuple[float, ...] | None
    firewalled_protected_contamination: tuple[float, ...] | None
    contamination_reduction_fraction: float | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _paths(modules: tuple[str, ...], flows: Sequence[InformationFlow], sources: set[str], targets: set[str], limit: int = 100) -> tuple[tuple[str, ...], ...]:
    adjacency = {module: [] for module in modules}
    for flow in flows:
        adjacency[flow.source].append(flow.target)
    found: list[tuple[str, ...]] = []
    for source in sources:
        stack = [(source, (source,))]
        while stack and len(found) < limit:
            node, path = stack.pop()
            if node in targets and len(path) > 1:
                found.append(path)
                continue
            for nxt in adjacency[node]:
                if nxt not in path:
                    stack.append((nxt, path + (nxt,)))
    return tuple(found)


def _minimum_cut(modules: tuple[str, ...], flows: Sequence[InformationFlow], sources: set[str], targets: set[str]) -> tuple[int, ...]:
    """Return edge indices of a minimum-cost directed source-target cut."""

    n = len(modules)
    index = {module: i for i, module in enumerate(modules)}
    super_source, super_sink = n, n + 1
    size = n + 2
    capacity = np.zeros((size, size), dtype=float)
    for flow in flows:
        capacity[index[flow.source], index[flow.target]] += flow.cut_cost
    finite_total = float(sum(flow.cut_cost for flow in flows))
    infinite = finite_total + 1.0
    for source in sources:
        capacity[super_source, index[source]] = infinite
    for target in targets:
        capacity[index[target], super_sink] = infinite

    residual = capacity.copy()
    while True:
        parent = np.full(size, -1, dtype=int)
        parent[super_source] = super_source
        queue = deque([super_source])
        while queue and parent[super_sink] < 0:
            u = queue.popleft()
            for v in np.flatnonzero(residual[u] > 1e-12):
                if parent[v] < 0:
                    parent[v] = u
                    queue.append(int(v))
        if parent[super_sink] < 0:
            break
        amount = float("inf")
        v = super_sink
        while v != super_source:
            u = int(parent[v]); amount = min(amount, residual[u, v]); v = u
        v = super_sink
        while v != super_source:
            u = int(parent[v]); residual[u, v] -= amount; residual[v, u] += amount; v = u

    reachable = {super_source}
    queue = deque([super_source])
    while queue:
        u = queue.popleft()
        for v in np.flatnonzero(residual[u] > 1e-12):
            if int(v) not in reachable:
                reachable.add(int(v)); queue.append(int(v))
    return tuple(
        i for i, flow in enumerate(flows)
        if index[flow.source] in reachable and index[flow.target] not in reachable
    )


def _contamination(modules: tuple[str, ...], flows: Sequence[InformationFlow], suspect_sources: set[str]) -> tuple[float, np.ndarray | None]:
    index = {module: i for i, module in enumerate(modules)}
    matrix = np.zeros((len(modules), len(modules)), dtype=float)
    for flow in flows:
        matrix[index[flow.target], index[flow.source]] += abs(flow.gain)
    radius = float(max(abs(np.linalg.eigvals(matrix)))) if matrix.size else 0.0
    if radius >= 1.0 - 1e-12:
        return radius, None
    shock = np.zeros(len(modules))
    for source in suspect_sources:
        shock[index[source]] = 1.0
    propagated = np.linalg.solve(np.eye(len(modules)) - matrix, shock)
    return radius, propagated


def design_inference_firewall(
    modules: Sequence[str],
    flows: Sequence[InformationFlow],
    *,
    suspect_sources: Sequence[str],
    protected_targets: Sequence[str],
) -> FirewallResult:
    """Find the least-cost information-flow cut isolating suspect from protected modules."""

    names = tuple(map(str, modules))
    if not names or len(set(names)) != len(names) or any(not name for name in names):
        raise ValueError("modules must be unique nonempty names")
    known = set(names)
    suspects = set(map(str, suspect_sources)); protected = set(map(str, protected_targets))
    if not suspects or not protected or not suspects <= known or not protected <= known:
        raise ValueError("suspect_sources and protected_targets must be nonempty module subsets")
    if suspects & protected:
        raise ValueError("a module cannot be both suspect and protected")
    flow_tuple = tuple(flows)
    for flow in flow_tuple:
        if flow.source not in known or flow.target not in known or flow.source == flow.target:
            raise ValueError("every flow must connect two different declared modules")
        if not np.isfinite(flow.gain) or flow.gain < 0 or not np.isfinite(flow.cut_cost) or flow.cut_cost <= 0:
            raise ValueError("flow gains must be finite nonnegative and cut costs finite positive")

    paths = _paths(names, flow_tuple, suspects, protected)
    cut_indices = _minimum_cut(names, flow_tuple, suspects, protected) if paths else ()
    cuts = tuple(flow_tuple[i] for i in cut_indices)
    remaining = tuple(flow for i, flow in enumerate(flow_tuple) if i not in set(cut_indices))
    full_radius, full_contamination = _contamination(names, flow_tuple, suspects)
    cut_radius, cut_contamination = _contamination(names, remaining, suspects)
    protected_indices = [names.index(target) for target in sorted(protected)]
    full_values = None if full_contamination is None else tuple(map(float, full_contamination[protected_indices]))
    cut_values = None if cut_contamination is None else tuple(map(float, cut_contamination[protected_indices]))
    if full_values is not None and cut_values is not None:
        full_total = sum(full_values); cut_total = sum(cut_values)
        reduction = None if full_total <= 1e-12 else float(1.0 - cut_total / full_total)
    else:
        reduction = None
    if not paths:
        status = "NO_SUSPECT_TO_PROTECTED_PATH"
    elif full_contamination is None and cut_contamination is not None:
        status = "FIREWALL_BREAKS_UNSTABLE_FEEDBACK"
    elif not _paths(names, remaining, suspects, protected):
        status = "MINIMUM_COST_FIREWALL_ISOLATES_PROTECTED_MODULES"
    else:
        status = "FIREWALL_INCOMPLETE"
    return FirewallResult(
        modules=names,
        suspect_sources=tuple(sorted(suspects)),
        protected_targets=tuple(sorted(protected)),
        exposed_paths=paths,
        cut_edges=cuts,
        total_cut_cost=float(sum(flow.cut_cost for flow in cuts)),
        full_loop_spectral_radius=full_radius,
        firewalled_loop_spectral_radius=cut_radius,
        full_protected_contamination=full_values,
        firewalled_protected_contamination=cut_values,
        contamination_reduction_fraction=reduction,
        status=status,
    )
