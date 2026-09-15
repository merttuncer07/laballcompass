"""Connected Deployable Bottleneck Locator (CDBL)."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class StockNode:
    name: str
    nominal_stock: float
    active_fraction: float = 1.0

    @property
    def active_stock(self) -> float:
        return self.nominal_stock * self.active_fraction


@dataclass(frozen=True)
class TransportEdge:
    name: str
    source: str
    target: str
    capacity: float
    lead_time: int
    yield_fraction: float = 1.0


@dataclass(frozen=True)
class DeploymentResult:
    nominal_stock: float
    active_stock: float
    deployable_to_target: float
    connectivity_conversion_ratio: float
    edge_flows: dict[str, float]


@dataclass(frozen=True)
class BottleneckImpact:
    kind: str
    name: str
    added_capacity: float
    delivery_gain: float
    marginal_gain: float


class ConnectedDeployableNetwork:
    """Solve generalized time-expanded material flow and perturb capacities."""

    def __init__(self, nodes: list[StockNode], edges: list[TransportEdge], target: str, horizon: int):
        self.nodes = {node.name: node for node in nodes}
        self.edges = list(edges)
        self.target = target
        self.horizon = int(horizon)
        if target not in self.nodes:
            raise ValueError("target node is missing")
        if any(edge.yield_fraction <= 0 or edge.yield_fraction > 1 for edge in edges):
            raise ValueError("edge yields must be in (0, 1]")

    def solve(self, demand: float | None = None) -> DeploymentResult:
        variables: list[tuple[int, int]] = []
        for edge_index, edge in enumerate(self.edges):
            for departure in range(self.horizon - edge.lead_time + 1):
                variables.append((edge_index, departure))
        count = len(variables)
        if count == 0:
            initial_target = self.nodes[self.target].active_stock
            delivered = min(initial_target, float(demand)) if demand is not None else initial_target
            nominal = sum(node.nominal_stock for name, node in self.nodes.items() if name != self.target)
            active = sum(node.active_stock for name, node in self.nodes.items() if name != self.target)
            return DeploymentResult(
                nominal_stock=float(nominal),
                active_stock=float(active),
                deployable_to_target=float(delivered),
                connectivity_conversion_ratio=float(delivered / nominal) if nominal > 0 else 0.0,
                edge_flows={edge.name: 0.0 for edge in self.edges},
            )
        objective = np.zeros(count)
        for variable, (edge_index, departure) in enumerate(variables):
            edge = self.edges[edge_index]
            if edge.target == self.target and departure + edge.lead_time <= self.horizon:
                objective[variable] = -edge.yield_fraction
        rows: list[np.ndarray] = []
        bounds: list[float] = []
        # A capacity belongs to the physical edge over the full planning horizon.
        for edge_index, edge in enumerate(self.edges):
            row = np.zeros(count)
            for variable, (candidate, _) in enumerate(variables):
                if candidate == edge_index:
                    row[variable] = 1.0
            rows.append(row)
            bounds.append(edge.capacity)
        # By every time t, cumulative departures cannot exceed local active
        # stock plus material that has already arrived (after conversion loss).
        for node_name, node in self.nodes.items():
            if node_name == self.target:
                continue
            for time in range(self.horizon + 1):
                row = np.zeros(count)
                for variable, (edge_index, departure) in enumerate(variables):
                    edge = self.edges[edge_index]
                    if edge.source == node_name and departure <= time:
                        row[variable] += 1.0
                    if edge.target == node_name and departure + edge.lead_time <= time:
                        row[variable] -= edge.yield_fraction
                rows.append(row)
                bounds.append(node.active_stock)
        initial_target = self.nodes[self.target].active_stock
        if demand is not None:
            row = -objective.copy()
            rows.append(row)
            bounds.append(max(0.0, float(demand) - initial_target))
        result = linprog(
            objective,
            A_ub=np.asarray(rows),
            b_ub=np.asarray(bounds),
            bounds=[(0.0, None)] * count,
            method="highs",
        )
        if not result.success:
            raise RuntimeError(result.message)
        delivered = initial_target - float(result.fun)
        edge_flows = {edge.name: 0.0 for edge in self.edges}
        for value, (edge_index, _) in zip(result.x, variables):
            edge_flows[self.edges[edge_index].name] += float(value)
        nominal = sum(node.nominal_stock for name, node in self.nodes.items() if name != self.target)
        active = sum(node.active_stock for name, node in self.nodes.items() if name != self.target)
        return DeploymentResult(
            nominal_stock=float(nominal),
            active_stock=float(active),
            deployable_to_target=float(delivered),
            connectivity_conversion_ratio=float(delivered / nominal) if nominal > 0 else 0.0,
            edge_flows=edge_flows,
        )

    def rank_bottlenecks(self, added_capacity: float = 10.0, demand: float | None = None) -> list[BottleneckImpact]:
        baseline = self.solve(demand).deployable_to_target
        impacts: list[BottleneckImpact] = []
        for edge_index, edge in enumerate(self.edges):
            expanded_edges = list(self.edges)
            expanded_edges[edge_index] = replace(edge, capacity=edge.capacity + added_capacity)
            gain = ConnectedDeployableNetwork(list(self.nodes.values()), expanded_edges, self.target, self.horizon).solve(
                demand
            ).deployable_to_target - baseline
            impacts.append(BottleneckImpact("edge", edge.name, added_capacity, gain, gain / added_capacity))
        for node_name, node in self.nodes.items():
            if node_name == self.target:
                continue
            expanded_nodes = list(self.nodes.values())
            index = next(i for i, candidate in enumerate(expanded_nodes) if candidate.name == node_name)
            if node.active_fraction > 0:
                expanded_nodes[index] = replace(
                    node, nominal_stock=node.nominal_stock + added_capacity / node.active_fraction
                )
            else:
                expanded_nodes[index] = replace(node, nominal_stock=added_capacity, active_fraction=1.0)
            gain = ConnectedDeployableNetwork(expanded_nodes, self.edges, self.target, self.horizon).solve(
                demand
            ).deployable_to_target - baseline
            impacts.append(BottleneckImpact("active_stock", node_name, added_capacity, gain, gain / added_capacity))
        return sorted(impacts, key=lambda item: (item.marginal_gain, item.delivery_gain), reverse=True)
