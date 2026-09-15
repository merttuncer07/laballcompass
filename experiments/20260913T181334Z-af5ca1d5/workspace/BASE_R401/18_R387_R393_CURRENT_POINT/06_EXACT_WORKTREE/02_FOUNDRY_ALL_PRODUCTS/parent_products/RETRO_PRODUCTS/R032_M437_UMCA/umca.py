"""Unbalanced Movement-Creation Accountant (UMCA).

Solve a linear unbalanced transport problem while keeping moved, destroyed,
and created mass as separate operational quantities.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class UnbalancedAccountingResult:
    flow: np.ndarray
    destroyed_at_source: np.ndarray
    created_at_target: np.ndarray
    moved_mass: float
    destroyed_mass: float
    created_mass: float
    movement_cost: float
    destruction_cost: float
    creation_cost: float
    total_cost: float
    source_balance_residual: float
    target_balance_residual: float


def solve_unbalanced_transport(
    source_mass: np.ndarray,
    target_mass: np.ndarray,
    movement_cost: np.ndarray,
    destruction_cost: np.ndarray | float,
    creation_cost: np.ndarray | float,
) -> UnbalancedAccountingResult:
    source = np.asarray(source_mass, dtype=float)
    target = np.asarray(target_mass, dtype=float)
    cost = np.asarray(movement_cost, dtype=float)
    if source.ndim != 1 or target.ndim != 1 or cost.shape != (source.size, target.size):
        raise ValueError("incompatible source, target, and cost dimensions")
    if np.any(source < 0) or np.any(target < 0) or np.any(cost < 0):
        raise ValueError("mass and costs must be nonnegative")
    destroy_cost = np.broadcast_to(np.asarray(destruction_cost, dtype=float), source.shape).copy()
    create_cost = np.broadcast_to(np.asarray(creation_cost, dtype=float), target.shape).copy()
    if np.any(destroy_cost < 0) or np.any(create_cost < 0):
        raise ValueError("mass-change costs must be nonnegative")

    flow_variables = source.size * target.size
    destroy_start = flow_variables
    create_start = destroy_start + source.size
    variable_count = create_start + target.size
    objective = np.concatenate([cost.ravel(), destroy_cost, create_cost])
    equalities = []
    rhs = []
    # Every source unit either moves or is explicitly destroyed.
    for i in range(source.size):
        row = np.zeros(variable_count)
        row[i * target.size : (i + 1) * target.size] = 1.0
        row[destroy_start + i] = 1.0
        equalities.append(row)
        rhs.append(source[i])
    # Every target unit either arrives or is explicitly created.
    for j in range(target.size):
        row = np.zeros(variable_count)
        row[j:flow_variables:target.size] = 1.0
        row[create_start + j] = 1.0
        equalities.append(row)
        rhs.append(target[j])
    solved = linprog(
        objective,
        A_eq=np.asarray(equalities),
        b_eq=np.asarray(rhs),
        bounds=[(0.0, None)] * variable_count,
        method="highs",
    )
    if not solved.success:
        raise RuntimeError(solved.message)
    flow = solved.x[:flow_variables].reshape(source.size, target.size)
    destroyed = solved.x[destroy_start:create_start]
    created = solved.x[create_start:]
    source_residual = float(np.max(np.abs(flow.sum(axis=1) + destroyed - source)))
    target_residual = float(np.max(np.abs(flow.sum(axis=0) + created - target)))
    movement_total = float(np.sum(flow * cost))
    destruction_total = float(destroyed @ destroy_cost)
    creation_total = float(created @ create_cost)
    return UnbalancedAccountingResult(
        flow=flow,
        destroyed_at_source=destroyed,
        created_at_target=created,
        moved_mass=float(flow.sum()),
        destroyed_mass=float(destroyed.sum()),
        created_mass=float(created.sum()),
        movement_cost=movement_total,
        destruction_cost=destruction_total,
        creation_cost=creation_total,
        total_cost=movement_total + destruction_total + creation_total,
        source_balance_residual=source_residual,
        target_balance_residual=target_residual,
    )


def normalized_balanced_baseline(
    source_mass: np.ndarray,
    target_mass: np.ndarray,
    movement_cost: np.ndarray,
) -> dict[str, object]:
    """Force equal totals by rescaling source mass, exposing the accounting loss."""
    source = np.asarray(source_mass, dtype=float)
    target = np.asarray(target_mass, dtype=float)
    cost = np.asarray(movement_cost, dtype=float)
    if source.sum() <= 0:
        raise ValueError("source total must be positive")
    factor = float(target.sum() / source.sum())
    rescaled = source * factor
    n, m = cost.shape
    objective = cost.ravel()
    equalities = []
    rhs = []
    for i in range(n):
        row = np.zeros(n * m)
        row[i * m : (i + 1) * m] = 1.0
        equalities.append(row)
        rhs.append(rescaled[i])
    for j in range(m):
        row = np.zeros(n * m)
        row[j : n * m : m] = 1.0
        equalities.append(row)
        rhs.append(target[j])
    solved = linprog(
        objective,
        A_eq=np.asarray(equalities),
        b_eq=np.asarray(rhs),
        bounds=[(0.0, None)] * (n * m),
        method="highs",
    )
    if not solved.success:
        raise RuntimeError(solved.message)
    flow = solved.x.reshape(n, m)
    return {
        "source_rescaling_factor": factor,
        "mass_reported_as_moved": float(flow.sum()),
        "mass_reported_as_created": 0.0,
        "mass_reported_as_destroyed": 0.0,
        "movement_cost": float(np.sum(flow * cost)),
        "flow": flow,
    }

