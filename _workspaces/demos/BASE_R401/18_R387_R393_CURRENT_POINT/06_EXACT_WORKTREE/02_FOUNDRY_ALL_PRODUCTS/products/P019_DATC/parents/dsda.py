"""Directional Subcritical-Damage Accumulator (DSDA)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DamageState:
    sequential_evidence: float
    contributing_cycles: int
    damage_proxy: float
    alarm: bool
    one_shot_alarm: bool


class DirectionalSubcriticalDamageAccumulator:
    """Accumulate capped same-direction evidence and a load-cycle damage proxy."""

    def __init__(
        self,
        design_shift: float = 0.30,
        evidence_threshold: float = 9.0,
        evidence_cap_per_cycle: float = 0.8,
        minimum_contributing_cycles: int = 12,
        evidence_retention: float = 0.999,
        one_shot_threshold: float = 3.5,
        endurance_load: float = 1.0,
        damage_exponent: float = 4.0,
        design_life: float = 220.0,
        damaging_direction: float = 1.0,
    ) -> None:
        self.design_shift = float(design_shift)
        self.threshold = float(evidence_threshold)
        self.cap = float(evidence_cap_per_cycle)
        self.minimum_cycles = int(minimum_contributing_cycles)
        self.retention = float(evidence_retention)
        self.one_shot_threshold = float(one_shot_threshold)
        self.endurance_load = float(endurance_load)
        self.damage_exponent = float(damage_exponent)
        self.design_life = float(design_life)
        self.direction = float(np.sign(damaging_direction) or 1.0)
        self.evidence = 0.0
        self.contributing_cycles = 0
        self.damage_proxy = 0.0
        self.alarm = False

    def update(self, standardized_residual: float, load_amplitude: float) -> DamageState:
        directed = self.direction * float(standardized_residual)
        severity = max(0.0, float(load_amplitude) / self.endurance_load)
        # Gaussian log-likelihood ratio for a small positive mean shift, with
        # load weighting and a hard per-cycle influence cap.
        increment = severity * (self.design_shift * directed - 0.5 * self.design_shift**2)
        increment = float(np.clip(increment, -self.cap, self.cap))
        self.evidence = max(0.0, self.retention * self.evidence + increment)
        if increment > 0:
            self.contributing_cycles += 1
        elif self.evidence == 0.0:
            self.contributing_cycles = 0
        self.damage_proxy += (severity**self.damage_exponent) / self.design_life
        self.alarm = self.alarm or (
            self.evidence >= self.threshold and self.contributing_cycles >= self.minimum_cycles
        )
        return DamageState(
            sequential_evidence=self.evidence,
            contributing_cycles=self.contributing_cycles,
            damage_proxy=self.damage_proxy,
            alarm=self.alarm,
            one_shot_alarm=directed >= self.one_shot_threshold,
        )

