"""Native-parent higher-order acquisition/representation budget experiment."""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np


LAB = Path(__file__).resolve().parents[2]
PRODUCTS = LAB / "R392_EXACT_BASE" / "01_V2_CORE" / "products"
for parent in (PRODUCTS / "V2P054_CADSBC", PRODUCTS / "V2P057_REOC"):
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))

from cadsbc import MODE_REGRET, Allocation, candidate as representation_candidate  # noqa: E402
from reoc import SensorSelection, select as observability_select  # noqa: E402


@dataclass(frozen=True)
class NativeBudgetDecision:
    sensor_budget: int
    representation_budget: int
    sensors: tuple[int, ...]
    modes: tuple[str, ...]
    additive_objective: float
    interaction_credit: float
    declared_joint_loss: float
    coupling: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _inputs(
    consequence: Sequence[float], sensor_rows: Sequence[Sequence[float]], total_budget: int
) -> tuple[np.ndarray, np.ndarray, int]:
    weights = np.asarray(consequence, dtype=float)
    rows = np.asarray(sensor_rows, dtype=float)
    if weights.ndim != 1 or weights.size < 2 or not np.all(np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError("consequence must be a finite nonnegative state vector")
    if rows.ndim != 2 or rows.shape[1] != weights.size or rows.shape[0] < 1 or not np.all(np.isfinite(rows)):
        raise ValueError("sensor geometry must align with consequence")
    if isinstance(total_budget, bool) or int(total_budget) != total_budget:
        raise ValueError("total budget must be an integer")
    budget = int(total_budget)
    if not 1 + weights.size <= budget <= rows.shape[0] + 3 * weights.size:
        raise ValueError("total budget is outside native-parent feasibility")
    return weights, rows, budget


def _terms(
    weights: np.ndarray,
    rows: np.ndarray,
    selection: SensorSelection,
    allocation: Allocation,
) -> tuple[float, float, float]:
    coverage = np.clip(np.sum(rows[list(selection.sensors)] ** 2, axis=0), 0.0, 1.0)
    residual = 1.0 - coverage
    regret = np.asarray([MODE_REGRET[mode] for mode in allocation.modes], dtype=float)
    additive = float(np.sum(weights * residual) + allocation.weighted_regret)
    interaction_credit = float(np.sum(weights * residual * regret))
    return additive, interaction_credit, additive - interaction_credit


def choose(
    consequence: Sequence[float],
    sensor_rows: Sequence[Sequence[float]],
    total_budget: int,
    *,
    coupling: float,
) -> NativeBudgetDecision:
    weights, rows, budget = _inputs(consequence, sensor_rows, total_budget)
    if not np.isfinite(coupling) or not 0.0 <= coupling <= 1.0:
        raise ValueError("coupling must lie in [0, 1]")

    feasible = []
    for sensor_budget in range(1, rows.shape[0] + 1):
        representation_budget = budget - sensor_budget
        if not weights.size <= representation_budget <= 3 * weights.size:
            continue
        selection = observability_select(weights, rows, sensor_budget)
        allocation = representation_candidate(weights, representation_budget)
        additive, interaction, joint = _terms(weights, rows, selection, allocation)
        feasible.append(
            (sensor_budget, representation_budget, selection, allocation, additive, interaction, joint)
        )
    if not feasible:
        raise RuntimeError("no native-parent split is feasible")
    effective_coupling = 0.0 if len(feasible) == 1 else float(coupling)
    chosen = min(
        feasible,
        key=lambda row: (
            row[4] - effective_coupling * row[5],
            row[0],
            row[2].sensors,
            row[3].modes,
        ),
    )
    sensor_budget, representation_budget, selection, allocation, additive, interaction, joint = chosen
    return NativeBudgetDecision(
        sensor_budget=int(sensor_budget),
        representation_budget=int(representation_budget),
        sensors=selection.sensors,
        modes=allocation.modes,
        additive_objective=float(additive),
        interaction_credit=float(interaction),
        declared_joint_loss=float(joint),
        coupling=effective_coupling,
        status=(
            "COLLAPSE_SINGLE_FEASIBLE_NATIVE_SPLIT"
            if len(feasible) == 1
            else ("NATIVE_JOINT_SPLIT" if effective_coupling else "NATIVE_REMOVAL_CONTROL")
        ),
    )


def candidate(consequence: Sequence[float], sensor_rows: Sequence[Sequence[float]], total_budget: int) -> NativeBudgetDecision:
    return choose(consequence, sensor_rows, total_budget, coupling=1.0)


def removal_control(consequence: Sequence[float], sensor_rows: Sequence[Sequence[float]], total_budget: int) -> NativeBudgetDecision:
    return choose(consequence, sensor_rows, total_budget, coupling=0.0)


def actual_joint_loss(
    decision: NativeBudgetDecision,
    sensor_rows: Sequence[Sequence[float]],
    truth_consequence: Sequence[float],
) -> float:
    truth = np.asarray(truth_consequence, dtype=float)
    rows = np.asarray(sensor_rows, dtype=float)
    if truth.ndim != 1 or rows.ndim != 2 or rows.shape[1] != truth.size:
        raise ValueError("truth consequence and sensor geometry must align")
    if not np.all(np.isfinite(truth)) or np.any(truth < 0) or not np.all(np.isfinite(rows)):
        raise ValueError("evaluation inputs must be finite and consequence nonnegative")
    coverage = np.clip(np.sum(rows[list(decision.sensors)] ** 2, axis=0), 0.0, 1.0)
    residual = 1.0 - coverage
    regret = np.asarray([MODE_REGRET[mode] for mode in decision.modes], dtype=float)
    return float(np.sum(truth * (residual + (1.0 - residual) * regret)))
