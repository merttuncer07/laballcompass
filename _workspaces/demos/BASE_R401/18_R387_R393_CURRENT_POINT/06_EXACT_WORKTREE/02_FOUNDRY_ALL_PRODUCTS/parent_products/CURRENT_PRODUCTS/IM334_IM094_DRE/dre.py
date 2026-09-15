"""Decision-Relevant Explorer, built from IM-334 -> IM-094."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Mapping, Sequence


def _phi(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def _Phi(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


@dataclass(frozen=True)
class GaussianArm:
    name: str
    mean: float
    variance: float
    observation_variance: float
    measurement_cost: float = 0.0

    def __post_init__(self) -> None:
        if self.variance <= 0 or self.observation_variance <= 0:
            raise ValueError("Posterior and observation variances must be positive")

    def update(self, observation: float) -> "GaussianArm":
        posterior_variance = 1.0 / (1.0 / self.variance + 1.0 / self.observation_variance)
        posterior_mean = posterior_variance * (
            self.mean / self.variance + observation / self.observation_variance
        )
        return replace(self, mean=posterior_mean, variance=posterior_variance)


@dataclass(frozen=True)
class ExplorationScore:
    arm: str
    immediate_value: float
    decision_crossing_value: float
    uncertainty_reduction_fraction: float
    future_information_value: float
    total_score: float


class DecisionRelevantExplorer:
    def score(self, arms: Sequence[GaussianArm], remaining_decisions: int) -> list[ExplorationScore]:
        if len(arms) < 2:
            raise ValueError("At least two actions are required")
        if remaining_decisions < 1:
            raise ValueError("remaining_decisions must be positive")
        scores = []
        for arm in arms:
            alternatives = [other.mean for other in arms if other.name != arm.name]
            reference = max(alternatives)
            gap = abs(arm.mean - reference)
            sigma = math.sqrt(arm.variance)
            z = gap / sigma
            crossing = sigma * _phi(z) - gap * _Phi(-z)
            next_variance = 1.0 / (1.0 / arm.variance + 1.0 / arm.observation_variance)
            reduction = 1.0 - math.sqrt(next_variance / arm.variance)
            future_value = remaining_decisions * crossing * reduction
            total = arm.mean + future_value - arm.measurement_cost
            scores.append(
                ExplorationScore(
                    arm.name, arm.mean, crossing, reduction, future_value, total
                )
            )
        return sorted(scores, key=lambda item: item.total_score, reverse=True)

    def choose(self, arms: Sequence[GaussianArm], remaining_decisions: int) -> str:
        return self.score(arms, remaining_decisions)[0].arm


def uncertainty_only_choice(arms: Sequence[GaussianArm]) -> str:
    return max(arms, key=lambda arm: arm.variance).name


def greedy_choice(arms: Sequence[GaussianArm]) -> str:
    return max(arms, key=lambda arm: arm.mean).name
