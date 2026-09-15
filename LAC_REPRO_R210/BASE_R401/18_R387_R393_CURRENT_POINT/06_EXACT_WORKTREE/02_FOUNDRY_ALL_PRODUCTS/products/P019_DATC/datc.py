"""Damage-accumulation trigger controller (DATC) v0.1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

if __package__:
    from .parents.dsda import DirectionalSubcriticalDamageAccumulator
else:
    from parents.dsda import DirectionalSubcriticalDamageAccumulator
if __package__:
    from .parents.dttc import DecisionTargetedTriggerDesigner, TriggerCandidate
else:
    from parents.dttc import DecisionTargetedTriggerDesigner, TriggerCandidate


@dataclass(frozen=True)
class FrozenDamageTrigger:
    candidate: str
    threshold: float
    design_objective: float


class DamageAwareTriggerController:
    def __init__(
        self,
        *,
        false_negative_cost: float = 5.0,
        false_positive_cost: float = 1.0,
        accumulator_parameters: Mapping[str, float | int] | None = None,
        threshold_grid_size: int = 201,
    ) -> None:
        self.fn_cost = float(false_negative_cost)
        self.fp_cost = float(false_positive_cost)
        self.accumulator_parameters = dict(accumulator_parameters or {})
        self.threshold_grid_size = int(threshold_grid_size)
        self.policy: FrozenDamageTrigger | None = None

    def sequential_signal(
        self,
        residuals: Sequence[float],
        load_amplitudes: Sequence[float],
    ) -> np.ndarray:
        residual = np.asarray(residuals, dtype=float)
        load = np.asarray(load_amplitudes, dtype=float)
        if residual.ndim != 1 or residual.shape != load.shape or len(residual) == 0:
            raise ValueError("residuals and loads must be equal non-empty vectors")
        if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(load)):
            raise ValueError("residuals and loads must be finite")
        accumulator = DirectionalSubcriticalDamageAccumulator(**self.accumulator_parameters)
        evidence = np.empty(len(residual))
        for i, (value, severity) in enumerate(zip(residual, load)):
            evidence[i] = accumulator.update(float(value), float(severity)).sequential_evidence
        return evidence

    def fit(
        self,
        *,
        residuals: Sequence[float],
        load_amplitudes: Sequence[float],
        protected_event: Sequence[bool],
        loss: Sequence[float],
    ) -> dict[str, Any]:
        raw = np.asarray(residuals, dtype=float)
        evidence = self.sequential_signal(raw, load_amplitudes)
        event = np.asarray(protected_event, dtype=bool)
        losses = np.asarray(loss, dtype=float)
        if event.shape != raw.shape or losses.shape != raw.shape:
            raise ValueError("event and loss must align with residuals")
        design = DecisionTargetedTriggerDesigner(
            self.fn_cost,
            self.fp_cost,
            threshold_grid_size=self.threshold_grid_size,
        ).design(
            [TriggerCandidate("raw_directed_residual"), TriggerCandidate("sequential_damage_evidence")],
            {
                "raw_directed_residual": raw,
                "sequential_damage_evidence": evidence,
            },
            event,
            losses,
        )
        selected = design["selected"]
        self.policy = FrozenDamageTrigger(
            selected["candidate"],
            float(selected["threshold"]),
            float(selected["objective"]),
        )
        return {"policy": self.policy, "design": design}

    def evaluate(
        self,
        *,
        residuals: Sequence[float],
        load_amplitudes: Sequence[float],
        protected_event: Sequence[bool],
    ) -> dict[str, float | str]:
        if self.policy is None:
            raise RuntimeError("fit must be called before evaluation")
        raw = np.asarray(residuals, dtype=float)
        evidence = self.sequential_signal(raw, load_amplitudes)
        event = np.asarray(protected_event, dtype=bool)
        if event.shape != raw.shape:
            raise ValueError("protected_event must align with residuals")
        signal = raw if self.policy.candidate == "raw_directed_residual" else evidence
        prediction = signal >= self.policy.threshold
        fn = float(np.mean(event & ~prediction))
        fp = float(np.mean(~event & prediction))
        return {
            "selected_candidate": self.policy.candidate,
            "selected_threshold": self.policy.threshold,
            "false_negative_rate": fn,
            "false_positive_rate": fp,
            "decision_objective": self.fn_cost * fn + self.fp_cost * fp,
        }
