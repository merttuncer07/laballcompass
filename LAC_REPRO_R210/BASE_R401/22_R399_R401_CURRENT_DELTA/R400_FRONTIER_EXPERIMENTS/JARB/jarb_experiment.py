"""Controlled higher-order experiment: joint acquisition/representation budgeting.

The candidate couples V2P057-style state observability and V2P054-style
representation regret.  The removal control keeps the same feasible decisions,
weights, costs and total budget but removes only their interaction term.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations, product
from typing import Sequence

import numpy as np


MODE_COST = np.asarray([1, 2, 3], dtype=int)
MODE_REGRET = np.asarray([1.0, 0.55, 0.20], dtype=float)
MODE_NAME = ("coarse", "balanced", "fine")


@dataclass(frozen=True)
class BudgetDecision:
    sensors: tuple[int, ...]
    modes: tuple[str, ...]
    spent_budget: int
    objective: float
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
    if rows.ndim != 2 or rows.shape[0] < 1 or rows.shape[1] != weights.size or not np.all(np.isfinite(rows)):
        raise ValueError("sensor rows must be a finite sensor-by-state matrix aligned to consequence")
    if np.any(rows < 0):
        raise ValueError("sensor geometry must be nonnegative")
    if isinstance(total_budget, bool) or int(total_budget) != total_budget:
        raise ValueError("total budget must be an integer")
    budget = int(total_budget)
    minimum = 1 + weights.size
    maximum = rows.shape[0] + 3 * weights.size
    if not minimum <= budget <= maximum:
        raise ValueError("total budget must fund at least one sensor and coarse representation")
    return weights, rows, budget


def _loss_terms(
    weights: np.ndarray, rows: np.ndarray, sensors: tuple[int, ...], mode_indices: tuple[int, ...]
) -> tuple[float, float, float]:
    coverage = np.clip(np.sum(rows[list(sensors)] ** 2, axis=0), 0.0, 1.0)
    residual = 1.0 - coverage
    regret = MODE_REGRET[list(mode_indices)]
    additive = float(np.sum(weights * (residual + regret)))
    interaction = float(np.sum(weights * residual * regret))
    joint = additive - interaction
    return additive, interaction, joint


def choose(
    consequence: Sequence[float],
    sensor_rows: Sequence[Sequence[float]],
    total_budget: int,
    *,
    coupling: float,
) -> BudgetDecision:
    weights, rows, budget = _inputs(consequence, sensor_rows, total_budget)
    if not np.isfinite(coupling) or not 0.0 <= coupling <= 1.0:
        raise ValueError("coupling must lie in [0, 1]")
    minimum = 1 + weights.size
    maximum = rows.shape[0] + 3 * weights.size
    effective_coupling = 0.0 if budget in (minimum, maximum) else float(coupling)

    if budget == maximum:
        sensors = tuple(range(rows.shape[0]))
        modes = tuple(2 for _ in range(weights.size))
        additive, interaction, joint = _loss_terms(weights, rows, sensors, modes)
        return BudgetDecision(
            sensors,
            tuple(MODE_NAME[index] for index in modes),
            maximum,
            additive - effective_coupling * interaction,
            joint,
            effective_coupling,
            "COLLAPSE_FULL_ACQUISITION_AND_FINE_REPRESENTATION",
        )

    candidates = []
    for sensor_count in range(1, rows.shape[0] + 1):
        for sensors in combinations(range(rows.shape[0]), sensor_count):
            for modes in product(range(3), repeat=weights.size):
                spent = sensor_count + int(np.sum(MODE_COST[list(modes)]))
                if spent > budget:
                    continue
                additive, interaction, joint = _loss_terms(weights, rows, sensors, modes)
                objective = additive - effective_coupling * interaction
                candidates.append((objective, spent, sensors, modes, joint))
    objective, spent, sensors, modes, joint = min(
        candidates, key=lambda row: (row[0], row[1], row[2], row[3])
    )
    return BudgetDecision(
        tuple(sensors),
        tuple(MODE_NAME[index] for index in modes),
        int(spent),
        float(objective),
        float(joint),
        effective_coupling,
        "COLLAPSE_MINIMUM_BUDGET" if budget == minimum else (
            "JOINT_BUDGET_CHANGED_DECISION" if effective_coupling else "REMOVAL_CONTROL"
        ),
    )


def candidate(consequence: Sequence[float], sensor_rows: Sequence[Sequence[float]], total_budget: int) -> BudgetDecision:
    return choose(consequence, sensor_rows, total_budget, coupling=1.0)


def removal_control(consequence: Sequence[float], sensor_rows: Sequence[Sequence[float]], total_budget: int) -> BudgetDecision:
    return choose(consequence, sensor_rows, total_budget, coupling=0.0)


def actual_joint_loss(
    decision: BudgetDecision,
    sensor_rows: Sequence[Sequence[float]],
    truth_consequence: Sequence[float],
) -> float:
    truth = np.asarray(truth_consequence, dtype=float)
    rows = np.asarray(sensor_rows, dtype=float)
    if truth.ndim != 1 or rows.ndim != 2 or rows.shape[1] != truth.size:
        raise ValueError("truth consequence and sensor geometry must align")
    if not np.all(np.isfinite(truth)) or np.any(truth < 0) or not np.all(np.isfinite(rows)):
        raise ValueError("evaluation inputs must be finite and consequence nonnegative")
    mode_indices = tuple(MODE_NAME.index(mode) for mode in decision.modes)
    return _loss_terms(truth, rows, decision.sensors, mode_indices)[2]
