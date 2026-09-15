"""Adaptive Consequence-Resolution Allocator, built from IM-406 -> IM-037."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class DecisionRegion:
    name: str
    time_importance: float
    frequency_importance: float
    consequence_weight: float


@dataclass(frozen=True)
class ResolutionOption:
    name: str
    cost: float
    time_error: float
    frequency_error: float


@dataclass(frozen=True)
class RegionAllocation:
    region: str
    option: str
    cost: float
    decision_loss: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdaptiveConsequenceResolutionAllocator:
    def __init__(
        self, regions: Sequence[DecisionRegion], options: Sequence[ResolutionOption]
    ) -> None:
        if not regions or not options:
            raise ValueError("At least one region and one resolution option are required")
        self.regions = tuple(regions)
        self.options = tuple(options)
        if len({r.name for r in self.regions}) != len(self.regions) or any(not r.name for r in self.regions):
            raise ValueError("Region names must be nonempty and unique")
        if len({o.name for o in self.options}) != len(self.options) or any(not o.name for o in self.options):
            raise ValueError("Resolution option names must be nonempty and unique")
        if any(
            not np.isfinite(value) or value < 0
            for region in regions
            for value in (region.time_importance, region.frequency_importance, region.consequence_weight)
        ):
            raise ValueError("Region importance and consequence values must be non-negative")
        if any(
            not np.isfinite(value) or value < 0
            for option in options
            for value in (option.cost, option.time_error, option.frequency_error)
        ):
            raise ValueError("Resolution cost and errors must be non-negative")

    @staticmethod
    def loss(region: DecisionRegion, option: ResolutionOption) -> float:
        return region.consequence_weight * (
            region.time_importance * option.time_error**2
            + region.frequency_importance * option.frequency_error**2
        )

    def allocate(self, budget: float) -> dict[str, Any]:
        if not np.isfinite(budget) or budget < 0:
            raise ValueError("budget must be non-negative")
        pairs = [(i, j) for i in range(len(self.regions)) for j in range(len(self.options))]
        objective = np.array([self.loss(self.regions[i], self.options[j]) for i, j in pairs])
        costs = np.array([self.options[j].cost for i, j in pairs])
        constraints = []
        for region_index in range(len(self.regions)):
            row = np.array([1.0 if i == region_index else 0.0 for i, j in pairs])
            constraints.append(LinearConstraint(row, 1.0, 1.0))
        constraints.append(LinearConstraint(costs, -np.inf, budget))
        result = milp(
            objective,
            integrality=np.ones(len(pairs)),
            bounds=Bounds(np.zeros(len(pairs)), np.ones(len(pairs))),
            constraints=constraints,
            options={"disp": False},
        )
        if not result.success:
            raise RuntimeError(f"Resolution allocation failed: {result.message}")
        allocations = []
        for selected, (i, j) in zip(result.x, pairs):
            if selected > 0.5:
                region = self.regions[i]
                option = self.options[j]
                allocations.append(
                    RegionAllocation(region.name, option.name, option.cost, self.loss(region, option))
                )
        return {
            "budget": budget,
            "total_cost": sum(item.cost for item in allocations),
            "total_decision_loss": sum(item.decision_loss for item in allocations),
            "allocations": [item.as_dict() for item in allocations],
        }

    def fixed_option(self, option_name: str) -> dict[str, Any]:
        option = next((item for item in self.options if item.name == option_name), None)
        if option is None:
            raise KeyError(f"Unknown option: {option_name}")
        allocations = [
            RegionAllocation(region.name, option.name, option.cost, self.loss(region, option))
            for region in self.regions
        ]
        return {
            "total_cost": sum(item.cost for item in allocations),
            "total_decision_loss": sum(item.decision_loss for item in allocations),
            "allocations": [item.as_dict() for item in allocations],
        }
