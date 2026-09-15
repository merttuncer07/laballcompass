"""Persistence-Qualified Decision Risk (PQDR) v0.1.

DTRM answers whether bounded uncertainty contains a perturbation direction that can
reverse a finite-horizon action gap. HMRM answers whether a state deviation loads on
consequence-bearing modes that recover slowly. PQDR composes them without conflating
time conventions:

    continuous generator G --expm(G * sample_interval)--> sampled transition T

The exact DTRM worst initial perturbation is then assessed by HMRM using the decision
contrast itself as the consequence map. This distinguishes a transient action-flip
direction from one embedded in a persistent decision-relevant mode.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np
from scipy.linalg import expm

if __package__:
    from .parents.dtrm import DecisionRiskResult, DecisionTransientRiskMonitor
else:
    from parents.dtrm import DecisionRiskResult, DecisionTransientRiskMonitor
if __package__:
    from .parents.hmrm import HiddenModeResilienceMonitor, ResilienceAssessment
else:
    from parents.hmrm import HiddenModeResilienceMonitor, ResilienceAssessment


def _square_matrix(values: Sequence[Sequence[float]], name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.shape[0] == 0:
        raise ValueError(f"{name} must be a non-empty square matrix")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be finite")
    return arr


def _vector(values: Sequence[float], n: int, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.shape != (n,) or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite vector of length {n}")
    return arr


@dataclass(frozen=True)
class PersistenceQualifiedRisk:
    status: str
    decision_risk: DecisionRiskResult
    persistence: ResilienceAssessment
    sample_interval: float
    sampled_transition: tuple[tuple[float, ...], ...]
    action_flip_possible: bool
    persistent_decision_mode: bool
    worst_perturbation_norm: float

    def as_dict(self) -> dict[str, Any]:
        out = asdict(self)
        # Keep parent dataclass semantics explicit in serialized output.
        out["decision_risk"] = self.decision_risk.as_dict()
        return out


class PersistenceQualifiedDecisionRiskMonitor:
    def __init__(
        self,
        *,
        uncertainty_map: Sequence[Sequence[float]],
        uncertainty_radius: float,
        horizon: float,
        sample_interval: float,
        minimum_exposure: float,
        minimum_recovery_steps: int,
        recovery_floor: float,
        scalar_alarm_distance: float,
        grid_points: int = 1001,
    ) -> None:
        if sample_interval <= 0 or not np.isfinite(sample_interval):
            raise ValueError("sample_interval must be finite and positive")
        self.sample_interval = float(sample_interval)
        self.dtrm = DecisionTransientRiskMonitor(
            uncertainty_map=uncertainty_map,
            uncertainty_radius=uncertainty_radius,
            horizon=horizon,
            grid_points=grid_points,
        )
        self.hmrm = HiddenModeResilienceMonitor(
            minimum_exposure=minimum_exposure,
            minimum_recovery_steps=minimum_recovery_steps,
            recovery_floor=recovery_floor,
            scalar_alarm_distance=scalar_alarm_distance,
        )

    def analyze_common_flow(
        self,
        *,
        system_generator: Sequence[Sequence[float]],
        decision_contrast: Sequence[float],
        nominal_gap: float,
        observed_direction: Sequence[float] | None = None,
        name: str = "preferred_vs_runner_up",
    ) -> PersistenceQualifiedRisk:
        generator = _square_matrix(system_generator, "system_generator")
        n = generator.shape[0]
        contrast = _vector(decision_contrast, n, "decision_contrast")
        observed = contrast if observed_direction is None else _vector(
            observed_direction, n, "observed_direction"
        )
        if self.dtrm.W.shape[0] != n:
            raise ValueError("system_generator and uncertainty_map state dimensions must match")

        decision = self.dtrm.analyze_common_flow(
            generator,
            contrast,
            nominal_gap,
            name=name,
        )
        worst = np.asarray(decision.worst_initial_perturbation, dtype=float)
        sampled_transition = expm(generator * self.sample_interval)
        # Decision contrast is a 1 x n consequence map: modes orthogonal to the
        # action gap receive zero consequence gain even if dynamically persistent.
        persistence = self.hmrm.assess(
            sampled_transition,
            worst,
            observed,
            consequence_matrix=np.atleast_2d(contrast),
        )
        action_flip = decision.status == "ACTION_FLIP_DIRECTION_EXISTS"
        persistent = bool(persistence.joint_alert)
        if action_flip and persistent:
            status = "PERSISTENT_ACTION_FLIP_RISK"
        elif action_flip:
            status = "TRANSIENT_ACTION_FLIP_RISK"
        elif persistent:
            status = "PERSISTENT_MODE_BUT_ACTION_CERTIFIED"
        else:
            status = "ACTION_CERTIFIED_NO_PERSISTENT_DECISION_MODE"

        return PersistenceQualifiedRisk(
            status=status,
            decision_risk=decision,
            persistence=persistence,
            sample_interval=self.sample_interval,
            sampled_transition=tuple(
                tuple(float(x) for x in row) for row in sampled_transition
            ),
            action_flip_possible=action_flip,
            persistent_decision_mode=persistent,
            worst_perturbation_norm=float(np.linalg.norm(worst)),
        )
