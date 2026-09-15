"""Conservation-Feasible Decision Risk (CFDR) v0.1.

DTRM analyzes bounded latent perturbations ``delta_x = W z, ||z|| <= r``.
If the physical system must remain on ``C x = c``, only perturbations satisfying
``C W z = 0`` are admissible. CFDR computes an orthonormal null-space basis N of
``C W`` and reruns DTRM with the exact restricted map ``W_feasible = W N``.

The worst conservation-feasible perturbation is then checked against CCVC's safe
set; when requested, CCVC filters a nominal control at that perturbed state.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np
from scipy.linalg import null_space

if __package__:
    from .parents.ccvc import ConservationConstrainedViability
else:
    from parents.ccvc import ConservationConstrainedViability
if __package__:
    from .parents.dtrm import DecisionRiskResult, DecisionTransientRiskMonitor
else:
    from parents.dtrm import DecisionRiskResult, DecisionTransientRiskMonitor


@dataclass(frozen=True)
class ConservationFeasibleDecisionRisk:
    status: str
    raw_risk: DecisionRiskResult
    feasible_risk: DecisionRiskResult
    raw_latent_dimension: int
    feasible_latent_dimension: int
    removed_latent_dimensions: int
    conservation_residual_of_worst_feasible_perturbation: float
    worst_feasible_state: tuple[float, ...]
    worst_feasible_state_in_safe_set: bool
    filtered_control: tuple[float, ...] | None

    def as_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["raw_risk"] = self.raw_risk.as_dict()
        out["feasible_risk"] = self.feasible_risk.as_dict()
        return out


class ConservationFeasibleDecisionRiskMonitor:
    def __init__(
        self,
        *,
        viability_model: ConservationConstrainedViability,
        uncertainty_map: Sequence[Sequence[float]],
        uncertainty_radius: float,
        horizon: float,
        grid_points: int = 1001,
        consistency_tolerance: float = 1e-9,
    ) -> None:
        self.viability = viability_model
        self.W = np.asarray(uncertainty_map, dtype=float)
        if self.W.ndim != 2 or self.W.shape[0] != self.viability.F.shape[0]:
            raise ValueError("uncertainty_map rows must match viability state dimension")
        if not np.all(np.isfinite(self.W)):
            raise ValueError("uncertainty_map must be finite")
        self.radius = float(uncertainty_radius)
        self.horizon = float(horizon)
        self.grid_points = int(grid_points)
        self.tol = float(consistency_tolerance)
        if self.tol <= 0:
            raise ValueError("consistency_tolerance must be positive")

    def _monitor(self, W: np.ndarray) -> DecisionTransientRiskMonitor:
        return DecisionTransientRiskMonitor(
            uncertainty_map=W,
            uncertainty_radius=self.radius,
            horizon=self.horizon,
            grid_points=self.grid_points,
        )

    def feasible_uncertainty_map(self) -> tuple[np.ndarray, np.ndarray]:
        """Return WN and the orthonormal latent null-space basis N."""
        latent_constraint = self.viability.C @ self.W
        basis = null_space(latent_constraint)
        feasible = self.W @ basis
        return feasible, basis

    def analyze_common_flow(
        self,
        *,
        system_matrix: Sequence[Sequence[float]],
        decision_contrast: Sequence[float],
        nominal_gap: float,
        nominal_state: Sequence[float],
        nominal_control: Sequence[float] | None = None,
        safety_step: float | None = None,
        name: str = "preferred_vs_runner_up",
    ) -> ConservationFeasibleDecisionRisk:
        A = np.asarray(system_matrix, dtype=float)
        if A.shape != self.viability.F.shape or not np.all(np.isfinite(A)):
            raise ValueError("system_matrix must match the viability drift matrix shape")
        if not np.allclose(A, self.viability.F, atol=self.tol, rtol=0.0):
            raise ValueError("DTRM and CCVC must use the same continuous system dynamics")
        state = np.asarray(nominal_state, dtype=float)
        if state.shape != (A.shape[0],) or not np.all(np.isfinite(state)):
            raise ValueError("nominal_state has wrong shape or non-finite values")
        if not self.viability.on_manifold(state, self.tol):
            raise ValueError("nominal_state must lie on the declared conservation manifold")
        if not self.viability.in_safe_set(state, self.tol):
            raise ValueError("nominal_state must start inside the declared safe set")

        raw = self._monitor(self.W).analyze_common_flow(
            A, decision_contrast, nominal_gap, name=name
        )
        feasible_W, basis = self.feasible_uncertainty_map()
        feasible = self._monitor(feasible_W).analyze_common_flow(
            A, decision_contrast, nominal_gap, name=name
        )

        delta = np.asarray(feasible.worst_initial_perturbation, dtype=float)
        worst_state = state + delta
        residual = float(np.max(np.abs(self.viability.C @ delta)))
        in_safe_set = bool(self.viability.in_safe_set(worst_state, self.tol))

        filtered: tuple[float, ...] | None = None
        if (nominal_control is None) ^ (safety_step is None):
            raise ValueError("nominal_control and safety_step must be supplied together")
        if nominal_control is not None and safety_step is not None and in_safe_set:
            safe_control = self.viability.filter_control(
                worst_state, np.asarray(nominal_control, dtype=float), float(safety_step)
            )
            filtered = tuple(float(x) for x in safe_control)

        raw_flip = raw.status == "ACTION_FLIP_DIRECTION_EXISTS"
        feasible_flip = feasible.status == "ACTION_FLIP_DIRECTION_EXISTS"
        if raw_flip and not feasible_flip:
            status = "CONSERVATION_REMOVES_RAW_ACTION_FLIP"
        elif feasible_flip and not in_safe_set:
            status = "CONSERVATION_FEASIBLE_FLIP_ALREADY_OUTSIDE_SAFE_SET"
        elif feasible_flip:
            status = "CONSERVATION_FEASIBLE_ACTION_FLIP"
        elif raw_flip:
            status = "RAW_FLIP_REDUCED_TO_BOUNDARY_OR_CERTIFIED"
        else:
            status = "ACTION_CERTIFIED_WITH_CONSERVATION"

        return ConservationFeasibleDecisionRisk(
            status=status,
            raw_risk=raw,
            feasible_risk=feasible,
            raw_latent_dimension=int(self.W.shape[1]),
            feasible_latent_dimension=int(basis.shape[1]),
            removed_latent_dimensions=int(self.W.shape[1] - basis.shape[1]),
            conservation_residual_of_worst_feasible_perturbation=residual,
            worst_feasible_state=tuple(float(x) for x in worst_state),
            worst_feasible_state_in_safe_set=in_safe_set,
            filtered_control=filtered,
        )
