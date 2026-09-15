"""Multi-Route Failure-Path Architect (MFPA)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np


@dataclass(frozen=True)
class DissipationMechanism:
    name: str
    activation_threshold: float
    specific_dissipation: float
    saturation_mass: float
    scenario_retention: dict[str, float]
    failure_family: str

    def capacity(self, mass: float, scenario: str) -> float:
        if mass <= 0:
            return 0.0
        retention = float(self.scenario_retention.get(scenario, 1.0))
        return float(
            retention
            * self.specific_dissipation
            * self.saturation_mass
            * (1.0 - np.exp(-mass / self.saturation_mass))
        )


@dataclass(frozen=True)
class ArchitectureResult:
    allocation: dict[str, float]
    scenario_failure_energy: dict[str, float]
    activated_routes: dict[str, tuple[str, ...]]
    worst_case_energy: float
    mean_energy: float
    failure_family_concentration: float


class MultiRouteFailurePathArchitect:
    """Allocate mass so sequential non-common-mode dissipation paths can activate."""

    def __init__(self, mechanisms: list[DissipationMechanism], scenarios: list[str], core_energy: float = 1.0):
        self.mechanisms = sorted(mechanisms, key=lambda item: item.activation_threshold)
        self.scenarios = list(scenarios)
        self.core_energy = float(core_energy)

    def evaluate(self, allocation: dict[str, float]) -> ArchitectureResult:
        energies: dict[str, float] = {}
        activated: dict[str, tuple[str, ...]] = {}
        for scenario in self.scenarios:
            resistance = self.core_energy
            used: list[str] = []
            for mechanism in self.mechanisms:
                mass = float(allocation.get(mechanism.name, 0.0))
                if mass <= 0:
                    continue
                # If the crack can outrun the architecture before this threshold,
                # the later route never gets a chance to dissipate energy.
                if mechanism.activation_threshold > resistance + 1e-12:
                    break
                resistance += mechanism.capacity(mass, scenario)
                used.append(mechanism.name)
            energies[scenario] = resistance
            activated[scenario] = tuple(used)
        family_mass: dict[str, float] = {}
        total_mass = sum(float(allocation.get(item.name, 0.0)) for item in self.mechanisms)
        for mechanism in self.mechanisms:
            family_mass[mechanism.failure_family] = family_mass.get(mechanism.failure_family, 0.0) + float(
                allocation.get(mechanism.name, 0.0)
            )
        concentration = (
            sum((mass / total_mass) ** 2 for mass in family_mass.values()) if total_mass > 0 else 1.0
        )
        return ArchitectureResult(
            allocation={item.name: float(allocation.get(item.name, 0.0)) for item in self.mechanisms},
            scenario_failure_energy=energies,
            activated_routes=activated,
            worst_case_energy=min(energies.values()),
            mean_energy=float(np.mean(list(energies.values()))),
            failure_family_concentration=float(concentration),
        )

    def optimize(self, total_mass: float, mass_step: float = 0.05) -> ArchitectureResult:
        units = int(round(total_mass / mass_step))
        if not np.isclose(units * mass_step, total_mass):
            raise ValueError("total mass must be divisible by mass_step")
        best: ArchitectureResult | None = None
        mechanism_count = len(self.mechanisms)
        # Integer compositions of `units` across all mechanisms.
        for prefix in product(range(units + 1), repeat=mechanism_count - 1):
            used = sum(prefix)
            if used > units:
                continue
            counts = (*prefix, units - used)
            allocation = {
                mechanism.name: count * mass_step for mechanism, count in zip(self.mechanisms, counts)
            }
            candidate = self.evaluate(allocation)
            score = (candidate.worst_case_energy, candidate.mean_energy, -candidate.failure_family_concentration)
            if best is None:
                best = candidate
            else:
                best_score = (best.worst_case_energy, best.mean_energy, -best.failure_family_concentration)
                if score > best_score:
                    best = candidate
        assert best is not None
        return best

    def best_single_route(self, total_mass: float) -> ArchitectureResult:
        candidates = [
            self.evaluate({candidate.name: total_mass}) for candidate in self.mechanisms
        ]
        return max(candidates, key=lambda item: (item.worst_case_energy, item.mean_energy))
