"""Calibration-aware trigger router (CATR) v0.1."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np

if __package__:
    from .parents.cwc import CalibrationWidthController
else:
    from parents.cwc import CalibrationWidthController
if __package__:
    from .parents.dttc import DecisionTargetedTriggerDesigner, TriggerCandidate
else:
    from parents.dttc import DecisionTargetedTriggerDesigner, TriggerCandidate


def vector(values: Sequence[float], name: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or len(result) == 0 or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be a non-empty finite vector")
    return result


@dataclass(frozen=True)
class FrozenTrigger:
    candidate: str
    threshold: float
    design_objective: float
    false_negative_cost: float
    false_positive_cost: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CalibrationAwareTriggerRouter:
    def __init__(
        self,
        *,
        target_coverage: float = 0.9,
        false_negative_cost: float = 1.0,
        false_positive_cost: float = 1.0,
        threshold_grid_size: int = 201,
    ) -> None:
        self.controller = CalibrationWidthController(target_coverage=target_coverage)
        self.fn_cost = float(false_negative_cost)
        self.fp_cost = float(false_positive_cost)
        self.threshold_grid_size = int(threshold_grid_size)
        self.policy: FrozenTrigger | None = None

    def _prequential_views(
        self,
        outcomes: Sequence[float],
        centers: Sequence[float],
        scales: Sequence[float],
    ) -> tuple[dict[str, np.ndarray], float]:
        y, c, s = vector(outcomes, "outcomes"), vector(centers, "centers"), vector(scales, "scales")
        if not (len(y) == len(c) == len(s)) or np.any(s <= 0):
            raise ValueError("outcomes, centers, and positive scales must align")
        upper = np.empty(len(y))
        covered = np.empty(len(y), dtype=bool)
        for i, (outcome, center, scale) in enumerate(zip(y, c, s)):
            # The endpoint exists before this outcome is observed.
            _, upper[i] = self.controller.interval(center, scale)
            observation = self.controller.observe(outcome, center, scale)
            covered[i] = observation.covered
        return {"center": c, "calibrated_upper": upper}, float(np.mean(covered))

    def fit(
        self,
        *,
        calibration_outcomes: Sequence[float],
        calibration_centers: Sequence[float],
        calibration_scales: Sequence[float],
        design_outcomes: Sequence[float],
        design_centers: Sequence[float],
        design_scales: Sequence[float],
        design_event: Sequence[bool],
        design_loss: Sequence[float],
    ) -> dict[str, Any]:
        self._prequential_views(calibration_outcomes, calibration_centers, calibration_scales)
        views, coverage = self._prequential_views(design_outcomes, design_centers, design_scales)
        event = np.asarray(design_event, dtype=bool)
        loss = vector(design_loss, "design_loss")
        if len(event) != len(loss) or len(event) != len(views["center"]):
            raise ValueError("design event/loss must align with forecasts")
        result = DecisionTargetedTriggerDesigner(
            self.fn_cost,
            self.fp_cost,
            threshold_grid_size=self.threshold_grid_size,
        ).design(
            [TriggerCandidate("center"), TriggerCandidate("calibrated_upper")],
            views,
            event,
            loss,
        )
        selected = result["selected"]
        self.policy = FrozenTrigger(
            candidate=selected["candidate"],
            threshold=float(selected["threshold"]),
            design_objective=float(selected["objective"]),
            false_negative_cost=self.fn_cost,
            false_positive_cost=self.fp_cost,
        )
        return {"policy": self.policy, "design": result, "design_coverage": coverage}

    def evaluate_prequential(
        self,
        *,
        outcomes: Sequence[float],
        centers: Sequence[float],
        scales: Sequence[float],
        event: Sequence[bool],
    ) -> dict[str, float | str]:
        if self.policy is None:
            raise RuntimeError("fit must be called before evaluation")
        views, coverage = self._prequential_views(outcomes, centers, scales)
        labels = np.asarray(event, dtype=bool)
        signal = views[self.policy.candidate]
        if len(labels) != len(signal):
            raise ValueError("event must align with forecasts")
        predicted = signal >= self.policy.threshold
        fn = float(np.mean(labels & ~predicted))
        fp = float(np.mean(~labels & predicted))
        return {
            "selected_candidate": self.policy.candidate,
            "selected_threshold": self.policy.threshold,
            "false_negative_rate": fn,
            "false_positive_rate": fp,
            "decision_objective": self.fn_cost * fn + self.fp_cost * fp,
            "coverage": coverage,
            "observations": len(signal),
        }
