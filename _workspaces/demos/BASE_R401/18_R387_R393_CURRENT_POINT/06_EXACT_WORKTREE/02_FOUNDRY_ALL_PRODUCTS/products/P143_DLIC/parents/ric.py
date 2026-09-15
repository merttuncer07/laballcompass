"""Relaxation Integrality Certifier (RIC)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp


@dataclass(frozen=True)
class TUCertificate:
    is_totally_unimodular: bool
    max_absolute_subdeterminant: int
    violating_size: int | None
    violating_rows: tuple[int, ...] | None
    violating_columns: tuple[int, ...] | None
    theorem_applies_with_integer_rhs: bool


@dataclass(frozen=True)
class RelaxationComparison:
    lp_solution: np.ndarray
    integer_solution: np.ndarray
    lp_objective: float
    integer_objective: float
    integrality_gap: float
    lp_solution_is_integral: bool


def certify_total_unimodularity(matrix: np.ndarray, integer_rhs: bool = True, max_dimension: int = 10) -> TUCertificate:
    """Exhaustively check every square subdeterminant for a small matrix."""
    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    if max(values.shape, default=0) > max_dimension:
        raise ValueError("exact exhaustive TU check exceeds configured dimension")
    if np.max(np.abs(values - np.rint(values)), initial=0.0) > 1e-10:
        return TUCertificate(False, 0, 1, None, None, False)
    integer_matrix = np.rint(values).astype(np.int64)
    largest = 0
    max_size = min(integer_matrix.shape)
    for size in range(1, max_size + 1):
        for rows in combinations(range(integer_matrix.shape[0]), size):
            for columns in combinations(range(integer_matrix.shape[1]), size):
                determinant = int(round(np.linalg.det(integer_matrix[np.ix_(rows, columns)])))
                magnitude = abs(determinant)
                largest = max(largest, magnitude)
                if magnitude > 1:
                    return TUCertificate(False, largest, size, rows, columns, False)
    return TUCertificate(True, largest, None, None, None, bool(integer_rhs))


def compare_lp_and_integer(
    objective: np.ndarray,
    inequality_matrix: np.ndarray | None = None,
    inequality_bound: np.ndarray | None = None,
    equality_matrix: np.ndarray | None = None,
    equality_bound: np.ndarray | None = None,
    lower_bound: np.ndarray | float = 0.0,
    upper_bound: np.ndarray | float = 1.0,
) -> RelaxationComparison:
    c = np.asarray(objective, dtype=float)
    a_ub = None if inequality_matrix is None else np.asarray(inequality_matrix, dtype=float)
    b_ub = None if inequality_bound is None else np.asarray(inequality_bound, dtype=float)
    a_eq = None if equality_matrix is None else np.asarray(equality_matrix, dtype=float)
    b_eq = None if equality_bound is None else np.asarray(equality_bound, dtype=float)
    lower = np.broadcast_to(np.asarray(lower_bound, dtype=float), c.shape).copy()
    upper = np.broadcast_to(np.asarray(upper_bound, dtype=float), c.shape).copy()
    lp = linprog(
        c,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=list(zip(lower, upper)),
        method="highs",
    )
    if not lp.success:
        raise RuntimeError(f"LP failed: {lp.message}")
    constraints = []
    if a_ub is not None:
        constraints.append(LinearConstraint(a_ub, -np.inf, b_ub))
    if a_eq is not None:
        constraints.append(LinearConstraint(a_eq, b_eq, b_eq))
    integer = milp(
        c,
        integrality=np.ones(c.size),
        bounds=Bounds(lower, upper),
        constraints=constraints,
    )
    if not integer.success:
        raise RuntimeError(f"integer solve failed: {integer.message}")
    return RelaxationComparison(
        lp_solution=np.asarray(lp.x),
        integer_solution=np.asarray(integer.x),
        lp_objective=float(lp.fun),
        integer_objective=float(integer.fun),
        integrality_gap=float(integer.fun - lp.fun),
        lp_solution_is_integral=bool(np.max(np.abs(lp.x - np.rint(lp.x))) <= 1e-8),
    )


def assignment_equalities(size: int) -> tuple[np.ndarray, np.ndarray]:
    """Return row/column sum equalities for a square assignment polytope."""
    rows = []
    for i in range(size):
        row = np.zeros(size * size)
        row[i * size : (i + 1) * size] = 1.0
        rows.append(row)
    for j in range(size):
        row = np.zeros(size * size)
        row[j : size * size : size] = 1.0
        rows.append(row)
    return np.asarray(rows), np.ones(2 * size)

