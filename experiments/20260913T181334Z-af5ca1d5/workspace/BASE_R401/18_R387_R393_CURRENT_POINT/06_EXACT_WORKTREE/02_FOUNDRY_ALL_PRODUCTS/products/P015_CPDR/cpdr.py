"""Conservation- and persistence-qualified decision risk (CPDR) v0.1.

CFDR first removes perturbation directions forbidden by an exact linear
conservation law. HMRM then qualifies the surviving worst perturbation by its
decision exposure and sampled recovery time. Persistence never creates a flip;
it only classifies a conservation-feasible DTRM flip.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np
from scipy.linalg import expm

if __package__:
    from .cfdr import ConservationFeasibleDecisionRisk, ConservationFeasibleDecisionRiskMonitor
else:
    from cfdr import ConservationFeasibleDecisionRisk, ConservationFeasibleDecisionRiskMonitor
if __package__:
    from .parents.hmrm import HiddenModeResilienceMonitor, ResilienceAssessment
else:
    from parents.hmrm import HiddenModeResilienceMonitor, ResilienceAssessment


@dataclass(frozen=True)
class ConservationPersistentRisk:
    status: str
    conservation_risk: ConservationFeasibleDecisionRisk
    persistence: ResilienceAssessment
    sample_interval: float
    sampled_transition: tuple[tuple[float, ...], ...]
    action_flip_feasible: bool
    persistent_decision_mode: bool

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["conservation_risk"] = self.conservation_risk.as_dict()
        return result


class ConservationPersistenceDecisionRiskMonitor:
    def __init__(
        self,
        *,
        conservation_monitor: ConservationFeasibleDecisionRiskMonitor,
        sample_interval: float,
        minimum_exposure: float,
        minimum_recovery_steps: int,
        recovery_floor: float,
        scalar_alarm_distance: float,
    ) -> None:
        if sample_interval <= 0 or not np.isfinite(sample_interval):
            raise ValueError("sample_interval must be finite and positive")
        self.conservation_monitor = conservation_monitor
        self.sample_interval = float(sample_interval)
        self.persistence_monitor = HiddenModeResilienceMonitor(
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
        nominal_state: Sequence[float],
        nominal_control: Sequence[float] | None = None,
        safety_step: float | None = None,
    ) -> ConservationPersistentRisk:
        generator = np.asarray(system_generator, dtype=float)
        contrast = np.asarray(decision_contrast, dtype=float)
        risk = self.conservation_monitor.analyze_common_flow(
            system_matrix=generator,
            decision_contrast=contrast,
            nominal_gap=nominal_gap,
            nominal_state=nominal_state,
            nominal_control=nominal_control,
            safety_step=safety_step,
        )
        worst = np.asarray(risk.feasible_risk.worst_initial_perturbation, dtype=float)
        sampled = expm(generator * self.sample_interval)
        persistence = self.persistence_monitor.assess(
            sampled,
            worst,
            contrast,
            consequence_matrix=np.atleast_2d(contrast),
        )
        raw_flip = risk.raw_risk.status == "ACTION_FLIP_DIRECTION_EXISTS"
        feasible_flip = risk.feasible_risk.status == "ACTION_FLIP_DIRECTION_EXISTS"
        persistent = bool(persistence.joint_alert)
        if raw_flip and not feasible_flip:
            status = "RAW_ACTION_FLIP_PHYSICALLY_INFEASIBLE"
        elif feasible_flip and persistent:
            status = "PERSISTENT_FEASIBLE_ACTION_FLIP_RISK"
        elif feasible_flip:
            status = "TRANSIENT_FEASIBLE_ACTION_FLIP_RISK"
        elif persistent:
            status = "PERSISTENT_MODE_WITHOUT_FEASIBLE_ACTION_FLIP"
        else:
            status = "ACTION_CERTIFIED_ON_CONSERVATION_MANIFOLD"
        return ConservationPersistentRisk(
            status=status,
            conservation_risk=risk,
            persistence=persistence,
            sample_interval=self.sample_interval,
            sampled_transition=tuple(tuple(float(x) for x in row) for row in sampled),
            action_flip_feasible=feasible_flip,
            persistent_decision_mode=persistent,
        )
