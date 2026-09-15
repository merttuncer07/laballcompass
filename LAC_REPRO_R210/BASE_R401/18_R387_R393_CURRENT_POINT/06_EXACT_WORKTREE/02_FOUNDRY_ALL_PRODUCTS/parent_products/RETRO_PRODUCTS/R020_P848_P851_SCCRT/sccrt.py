"""State-bearing Catalyst Cycle and Regeneration Tracker (SCCRT) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class CatalystCycleResult:
    times: tuple[float, ...]
    active_lattice_fraction: tuple[float, ...]
    product_per_step: tuple[float, ...]
    regeneration_per_step: tuple[float, ...]
    total_product: float
    total_lattice_species_consumed: float
    total_lattice_species_restored: float
    final_active_fraction: float
    minimum_active_fraction: float
    passive_catalyst_product_prediction: float
    passive_overprediction_fraction: float
    material_balance_error: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RegenerationDesign:
    selected_oxidant_scale: float
    selected: CatalystCycleResult
    candidates: tuple[tuple[float, CatalystCycleResult], ...]
    feasible: bool
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_catalyst_cycle(
    reactant_feed: Sequence[float],
    oxidant_feed: Sequence[float],
    *,
    time_step: float,
    reaction_rate_constant: float,
    regeneration_rate_constant: float,
    catalyst_lattice_capacity: float,
    initial_active_fraction: float = 1.0,
    minimum_operating_active_fraction: float = 0.2,
) -> CatalystCycleResult:
    """Track lattice-species consumption and restoration instead of assuming a passive catalyst."""

    reactant = np.asarray(reactant_feed, dtype=float); oxidant = np.asarray(oxidant_feed, dtype=float)
    if reactant.ndim != 1 or oxidant.shape != reactant.shape or reactant.size < 1 or np.any(reactant < 0) or np.any(oxidant < 0) or not np.all(np.isfinite(reactant)) or not np.all(np.isfinite(oxidant)):
        raise ValueError("feed schedules must be matching finite nonnegative vectors")
    if time_step <= 0 or reaction_rate_constant < 0 or regeneration_rate_constant < 0 or catalyst_lattice_capacity <= 0:
        raise ValueError("time/capacity must be positive and rate constants nonnegative")
    if not 0 <= initial_active_fraction <= 1 or not 0 <= minimum_operating_active_fraction <= 1:
        raise ValueError("active fractions must lie in [0,1]")
    active = float(initial_active_fraction)
    active_history = [active]; product = []; restored_history = []
    consumed_total = restored_total = 0.0
    passive_total = 0.0
    for reactant_level, oxidant_level in zip(reactant, oxidant):
        requested_consumption = reaction_rate_constant * reactant_level * active * time_step
        consumed_fraction = min(active, float(requested_consumption))
        active_after_reaction = active - consumed_fraction
        vacancy = 1.0 - active_after_reaction
        requested_restore = regeneration_rate_constant * oxidant_level * vacancy * time_step
        restored_fraction = min(vacancy, float(requested_restore))
        active = active_after_reaction + restored_fraction
        consumed = consumed_fraction * catalyst_lattice_capacity
        restored = restored_fraction * catalyst_lattice_capacity
        product.append(consumed); restored_history.append(restored)
        consumed_total += consumed; restored_total += restored
        passive_total += reaction_rate_constant * reactant_level * time_step * catalyst_lattice_capacity
        active_history.append(active)
    expected_final_inventory = initial_active_fraction * catalyst_lattice_capacity - consumed_total + restored_total
    actual_final_inventory = active * catalyst_lattice_capacity
    balance_error = actual_final_inventory - expected_final_inventory
    overprediction = 0.0 if consumed_total <= 0 else passive_total / consumed_total - 1.0
    minimum = float(min(active_history))
    if minimum < minimum_operating_active_fraction:
        status = "REGENERATION_CAPACITY_INSUFFICIENT"
    elif active >= initial_active_fraction - .05:
        status = "CATALYTIC_STATE_CYCLE_SUSTAINED"
    else:
        status = "CYCLE_OPERATES_WITH_NET_LATTICE_DEPLETION"
    return CatalystCycleResult(
        times=tuple(float(i * time_step) for i in range(reactant.size + 1)),
        active_lattice_fraction=tuple(map(float, active_history)),
        product_per_step=tuple(map(float, product)),
        regeneration_per_step=tuple(map(float, restored_history)),
        total_product=float(consumed_total),
        total_lattice_species_consumed=float(consumed_total),
        total_lattice_species_restored=float(restored_total),
        final_active_fraction=float(active),
        minimum_active_fraction=minimum,
        passive_catalyst_product_prediction=float(passive_total),
        passive_overprediction_fraction=float(overprediction),
        material_balance_error=float(balance_error),
        status=status,
    )


def design_regeneration_capacity(
    reactant_feed: Sequence[float],
    base_oxidant_feed: Sequence[float],
    oxidant_scale_candidates: Sequence[float],
    *,
    required_minimum_active_fraction: float,
    required_final_active_fraction: float,
    **simulation_parameters,
) -> RegenerationDesign:
    """Select the smallest declared oxidant scale that sustains the requested catalyst state."""

    scales = sorted(set(map(float, oxidant_scale_candidates)))
    if not scales or min(scales) < 0 or not 0 <= required_minimum_active_fraction <= 1 or not 0 <= required_final_active_fraction <= 1:
        raise ValueError("invalid scale candidates or required fractions")
    base = np.asarray(base_oxidant_feed, dtype=float)
    candidates = tuple(
        (scale, simulate_catalyst_cycle(
            reactant_feed, base * scale,
            minimum_operating_active_fraction=required_minimum_active_fraction,
            **simulation_parameters,
        ))
        for scale in scales
    )
    feasible = [item for item in candidates if item[1].minimum_active_fraction >= required_minimum_active_fraction and item[1].final_active_fraction >= required_final_active_fraction]
    if feasible:
        selected = feasible[0]; status = "MINIMUM_REGENERATION_CAPACITY_FOUND"; is_feasible = True
    else:
        selected = max(candidates, key=lambda item: (item[1].final_active_fraction, item[1].minimum_active_fraction)); status = "NO_DECLARED_SCALE_SUSTAINS_REQUIRED_STATE"; is_feasible = False
    return RegenerationDesign(float(selected[0]), selected[1], candidates, is_feasible, status)
