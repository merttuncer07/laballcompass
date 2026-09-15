"""Decision-Targeted Trigger Channel designer, built from IM-455 -> IM-094."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class TriggerCandidate:
    name: str
    verification_cost: float = 0.0
    manipulation_exposure: float = 0.0


@dataclass(frozen=True)
class TriggerDesignResult:
    candidate: str
    threshold: float
    objective: float
    false_negative_rate: float
    false_positive_rate: float
    verification_cost: float
    manipulation_cost: float
    correlation_with_loss: float
    event_rate: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finite_vector(values: Sequence[float], name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.ndim != 1 or len(vector) == 0 or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must be a non-empty finite vector")
    return vector


class DecisionTargetedTriggerDesigner:
    def __init__(
        self,
        false_negative_cost: float,
        false_positive_cost: float,
        manipulation_cost_weight: float = 1.0,
        threshold_grid_size: int = 201,
    ) -> None:
        if false_negative_cost < 0 or false_positive_cost < 0:
            raise ValueError("Action-error costs must be non-negative")
        if manipulation_cost_weight < 0:
            raise ValueError("manipulation_cost_weight must be non-negative")
        if threshold_grid_size < 3:
            raise ValueError("threshold_grid_size must be at least three")
        self.fn_cost = float(false_negative_cost)
        self.fp_cost = float(false_positive_cost)
        self.manipulation_weight = float(manipulation_cost_weight)
        self.grid_size = threshold_grid_size

    def _thresholds(self, signal: np.ndarray) -> np.ndarray:
        quantiles = np.linspace(0.0, 1.0, self.grid_size)
        thresholds = np.unique(np.quantile(signal, quantiles))
        spread = max(1.0, float(np.ptp(signal)))
        return np.concatenate(
            ([float(signal.min() - spread)], thresholds, [float(signal.max() + spread)])
        )

    def fit_candidate(
        self,
        candidate: TriggerCandidate,
        signal: Sequence[float],
        protected_event: Sequence[bool],
        loss: Sequence[float],
    ) -> TriggerDesignResult:
        x = _finite_vector(signal, "signal")
        y = np.asarray(protected_event, dtype=bool)
        losses = _finite_vector(loss, "loss")
        if len(x) != len(y) or len(x) != len(losses):
            raise ValueError("signal, event, and loss lengths must match")

        best: tuple[float, float, float, float] | None = None
        fixed_manipulation_cost = self.manipulation_weight * candidate.manipulation_exposure
        for threshold in self._thresholds(x):
            predicted = x >= threshold
            fn = float(np.mean(y & ~predicted))
            fp = float(np.mean(~y & predicted))
            objective = (
                self.fn_cost * fn
                + self.fp_cost * fp
                + candidate.verification_cost
                + fixed_manipulation_cost
            )
            row = (objective, float(threshold), fn, fp)
            if best is None or row < best:
                best = row
        assert best is not None
        objective, threshold, fn, fp = best
        correlation = float(np.corrcoef(losses, x)[0, 1])
        return TriggerDesignResult(
            candidate=candidate.name,
            threshold=threshold,
            objective=objective,
            false_negative_rate=fn,
            false_positive_rate=fp,
            verification_cost=candidate.verification_cost,
            manipulation_cost=fixed_manipulation_cost,
            correlation_with_loss=correlation,
            event_rate=float(np.mean(y)),
        )

    def design(
        self,
        candidates: Sequence[TriggerCandidate],
        signals: Mapping[str, Sequence[float]],
        protected_event: Sequence[bool],
        loss: Sequence[float],
    ) -> dict[str, Any]:
        if not candidates:
            raise ValueError("At least one trigger candidate is required")
        results = [
            self.fit_candidate(candidate, signals[candidate.name], protected_event, loss)
            for candidate in candidates
        ]
        results.sort(key=lambda result: result.objective)
        return {
            "selected": results[0].as_dict(),
            "ranking": [result.as_dict() for result in results],
            "objective_definition": {
                "false_negative_cost": self.fn_cost,
                "false_positive_cost": self.fp_cost,
                "manipulation_cost_weight": self.manipulation_weight,
            },
        }


def design_from_config(config: Mapping[str, Any], columns: Mapping[str, Sequence[Any]]) -> dict[str, Any]:
    loss = np.asarray(columns[config["loss_column"]], dtype=float)
    protected_event = loss > float(config["protected_loss_threshold"])
    candidates = [
        TriggerCandidate(
            name=item["column"],
            verification_cost=float(item.get("verification_cost", 0.0)),
            manipulation_exposure=float(item.get("manipulation_exposure", 0.0)),
        )
        for item in config["candidates"]
    ]
    designer = DecisionTargetedTriggerDesigner(
        false_negative_cost=float(config["false_negative_cost"]),
        false_positive_cost=float(config["false_positive_cost"]),
        manipulation_cost_weight=float(config.get("manipulation_cost_weight", 1.0)),
        threshold_grid_size=int(config.get("threshold_grid_size", 201)),
    )
    signals = {candidate.name: columns[candidate.name] for candidate in candidates}
    return designer.design(candidates, signals, protected_event, loss)


def save_result(result: Mapping[str, Any], output: Path) -> None:
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
