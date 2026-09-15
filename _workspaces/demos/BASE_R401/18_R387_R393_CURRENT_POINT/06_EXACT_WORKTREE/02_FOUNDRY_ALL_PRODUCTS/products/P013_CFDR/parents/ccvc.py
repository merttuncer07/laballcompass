"""Conservation-Constrained Viability Certifier (CCVC).

The product combines an affine controlled vector field with an equality-defined
conservation manifold and a polyhedral safe set.  It can certify local viable
directions and filter a nominal control through a one-step safety constraint.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
from scipy.optimize import linprog, minimize


@dataclass(frozen=True)
class LocalCertificate:
    feasible: bool
    control: np.ndarray | None
    inward_margin: float
    active_constraints: tuple[int, ...]
    conservation_residual: float


class ConservationConstrainedViability:
    """Certify and enforce viability for ``xdot = drift(x) + B u``."""

    def __init__(
        self,
        drift_matrix: np.ndarray,
        control_matrix: np.ndarray,
        conservation_matrix: np.ndarray,
        conservation_value: np.ndarray,
        safe_matrix: np.ndarray,
        safe_bound: np.ndarray,
        control_lower: np.ndarray,
        control_upper: np.ndarray,
    ) -> None:
        self.F = np.asarray(drift_matrix, dtype=float)
        self.B = np.asarray(control_matrix, dtype=float)
        self.C = np.atleast_2d(np.asarray(conservation_matrix, dtype=float))
        self.c = np.atleast_1d(np.asarray(conservation_value, dtype=float))
        self.A = np.atleast_2d(np.asarray(safe_matrix, dtype=float))
        self.b = np.atleast_1d(np.asarray(safe_bound, dtype=float))
        self.u_lower = np.atleast_1d(np.asarray(control_lower, dtype=float))
        self.u_upper = np.atleast_1d(np.asarray(control_upper, dtype=float))
        n = self.F.shape[0]
        if self.F.shape != (n, n) or self.B.shape[0] != n or self.C.shape[1] != n:
            raise ValueError("incompatible system dimensions")
        if self.A.shape[1] != n or self.A.shape[0] != self.b.size:
            raise ValueError("incompatible safe-set dimensions")
        if self.B.shape[1] != self.u_lower.size or self.u_lower.shape != self.u_upper.shape:
            raise ValueError("incompatible control dimensions")

    def drift(self, state: np.ndarray) -> np.ndarray:
        return self.F @ np.asarray(state, dtype=float)

    def velocity(self, state: np.ndarray, control: np.ndarray) -> np.ndarray:
        return self.drift(state) + self.B @ np.asarray(control, dtype=float)

    def on_manifold(self, state: np.ndarray, tolerance: float = 1e-8) -> bool:
        return bool(np.max(np.abs(self.C @ state - self.c)) <= tolerance)

    def in_safe_set(self, state: np.ndarray, tolerance: float = 1e-8) -> bool:
        return bool(np.max(self.A @ state - self.b) <= tolerance)

    def vertices(self, tolerance: float = 1e-8) -> list[np.ndarray]:
        """Enumerate vertices of ``C x = c, A x <= b`` for small products."""
        n = self.F.shape[0]
        rank_c = np.linalg.matrix_rank(self.C)
        needed = n - rank_c
        found: list[np.ndarray] = []
        for active in combinations(range(self.A.shape[0]), needed):
            matrix = np.vstack([self.C, self.A[list(active)]])
            rhs = np.concatenate([self.c, self.b[list(active)]])
            if matrix.shape[0] != n or np.linalg.matrix_rank(matrix) < n:
                continue
            point = np.linalg.solve(matrix, rhs)
            if self.in_safe_set(point, tolerance) and self.on_manifold(point, tolerance):
                if not any(np.linalg.norm(point - old, ord=np.inf) <= tolerance for old in found):
                    found.append(point)
        return found

    def local_certificate(
        self,
        state: np.ndarray,
        boundary_tolerance: float = 1e-7,
    ) -> LocalCertificate:
        """Maximize the common inward velocity margin at active boundaries.

        Conservation tangency is imposed as an equality.  At each active safe
        boundary ``a_i x = b_i``, the LP requires ``a_i xdot <= -margin``.
        """
        x = np.asarray(state, dtype=float)
        if not self.on_manifold(x, boundary_tolerance) or not self.in_safe_set(x, boundary_tolerance):
            return LocalCertificate(False, None, float("-inf"), (), float("inf"))
        slack = self.b - self.A @ x
        active = tuple(np.flatnonzero(slack <= boundary_tolerance).tolist())
        m = self.B.shape[1]
        objective = np.zeros(m + 1)
        objective[-1] = -1.0
        a_ub = []
        b_ub = []
        drift = self.drift(x)
        for index in active:
            row = np.zeros(m + 1)
            row[:m] = self.A[index] @ self.B
            row[-1] = 1.0
            a_ub.append(row)
            b_ub.append(-float(self.A[index] @ drift))
        a_eq = np.hstack([self.C @ self.B, np.zeros((self.C.shape[0], 1))])
        b_eq = -(self.C @ drift)
        bounds = list(zip(self.u_lower, self.u_upper)) + [(None, None)]
        result = linprog(
            objective,
            A_ub=np.asarray(a_ub) if a_ub else None,
            b_ub=np.asarray(b_ub) if b_ub else None,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )
        if not result.success:
            return LocalCertificate(False, None, float("-inf"), active, float("inf"))
        u = result.x[:m]
        residual = float(np.max(np.abs(self.C @ self.velocity(x, u))))
        return LocalCertificate(True, u, float(result.x[-1]), active, residual)

    def certify_vertices(self, tolerance: float = 1e-8) -> dict[str, object]:
        points = self.vertices(tolerance)
        certificates = [self.local_certificate(point, max(tolerance, 1e-7)) for point in points]
        viable = bool(points) and all(item.feasible and item.inward_margin >= -tolerance for item in certificates)
        return {
            "viable": viable,
            "vertex_count": len(points),
            "minimum_inward_margin": min((item.inward_margin for item in certificates), default=float("-inf")),
            "maximum_conservation_residual": max(
                (item.conservation_residual for item in certificates), default=float("inf")
            ),
            "vertices": points,
            "certificates": certificates,
        }

    def filter_control(
        self,
        state: np.ndarray,
        nominal_control: np.ndarray,
        step: float,
    ) -> np.ndarray:
        """Return the nearest bounded control whose Euler step remains viable."""
        x = np.asarray(state, dtype=float)
        nominal = np.clip(np.asarray(nominal_control, dtype=float), self.u_lower, self.u_upper)
        drift = self.drift(x)
        conservation_control = self.C @ self.B
        conservation_rhs = -(self.C @ drift)

        # Do not hand an optimizer redundant identities such as 0 @ u = 0.
        # They are common when the drift and every actuator are structurally
        # tangent to the conservation manifold, and they make SLSQP singular.
        effective_rows: list[int] = []
        current = np.empty((0, conservation_control.shape[1]))
        for row_index, row in enumerate(conservation_control):
            if np.linalg.norm(row) <= 1e-12:
                if abs(conservation_rhs[row_index]) > 1e-10:
                    raise RuntimeError("the drift leaves the conservation manifold and controls cannot correct it")
                continue
            candidate = np.vstack([current, row])
            if np.linalg.matrix_rank(candidate, tol=1e-11) > np.linalg.matrix_rank(current, tol=1e-11):
                effective_rows.append(row_index)
                current = candidate

        def objective(u: np.ndarray) -> float:
            delta = u - nominal
            return 0.5 * float(delta @ delta)

        constraints = [
            {
                "type": "ineq",
                "fun": lambda u: self.b - self.A @ (x + step * (drift + self.B @ u)),
            },
        ]
        if effective_rows:
            eq_matrix = conservation_control[effective_rows]
            eq_rhs = conservation_rhs[effective_rows]
            constraints.append(
                {
                    "type": "eq",
                    "fun": lambda u, matrix=eq_matrix, rhs=eq_rhs: matrix @ u - rhs,
                }
            )
        result = minimize(
            objective,
            nominal,
            method="SLSQP",
            bounds=list(zip(self.u_lower, self.u_upper)),
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 300},
        )
        if not result.success:
            raise RuntimeError(f"no safe control found: {result.message}")
        return np.asarray(result.x, dtype=float)
