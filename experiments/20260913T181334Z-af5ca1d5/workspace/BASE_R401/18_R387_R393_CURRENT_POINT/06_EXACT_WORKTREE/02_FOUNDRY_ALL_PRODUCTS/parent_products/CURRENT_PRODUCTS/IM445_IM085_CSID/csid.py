"""Contract Safeguard Independence Designer, built from IM-445 -> IM-085."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class FailureMode:
    name: str
    probability: float
    consequence: float

    def __post_init__(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("Failure probability must be between zero and one")
        if not math.isfinite(self.consequence) or self.consequence < 0:
            raise ValueError("Failure consequence must be non-negative")


@dataclass(frozen=True)
class Safeguard:
    name: str
    cost: float
    evidence_family: str
    coverage: Mapping[str, float]

    def __post_init__(self) -> None:
        if not math.isfinite(self.cost) or self.cost < 0:
            raise ValueError("Safeguard cost must be non-negative")
        if not self.evidence_family.strip():
            raise ValueError("evidence_family cannot be empty")
        if any(not math.isfinite(value) or value < 0 or value > 1 for value in self.coverage.values()):
            raise ValueError("Coverage values must be between zero and one")


@dataclass(frozen=True)
class PortfolioResult:
    safeguards: tuple[str, ...]
    total_cost: float
    expected_residual_loss: float
    objective: float
    evidence_families: tuple[str, ...]
    coverage_by_failure: Mapping[str, float]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContractSafeguardDesigner:
    """Choose safeguards without counting common evidence twice."""

    def __init__(self, failure_modes: Sequence[FailureMode], safeguards: Sequence[Safeguard]) -> None:
        if not failure_modes:
            raise ValueError("At least one failure mode is required")
        self.failures = tuple(failure_modes)
        self.safeguards = tuple(safeguards)
        failure_names = {failure.name for failure in self.failures}
        if len(failure_names) != len(self.failures) or any(not n for n in failure_names):
            raise ValueError("Failure names must be nonempty and unique")
        if len({s.name for s in self.safeguards}) != len(self.safeguards) or any(not s.name for s in self.safeguards):
            raise ValueError("Safeguard names must be nonempty and unique")
        unknown = {
            key
            for safeguard in self.safeguards
            for key in safeguard.coverage
            if key not in failure_names
        }
        if unknown:
            raise ValueError(f"Coverage references unknown failures: {sorted(unknown)}")

    @staticmethod
    def _combined_coverage(
        selected: Sequence[Safeguard], failure_name: str, family_aware: bool
    ) -> float:
        if not selected:
            return 0.0
        if family_aware:
            # Safeguards sharing one evidence family can fail together.  Keep
            # only the strongest coverage within that family; combine distinct
            # evidence families multiplicatively.
            by_family: dict[str, float] = {}
            for safeguard in selected:
                coverage = float(safeguard.coverage.get(failure_name, 0.0))
                by_family[safeguard.evidence_family] = max(
                    by_family.get(safeguard.evidence_family, 0.0), coverage
                )
            miss_probability = 1.0
            for coverage in by_family.values():
                miss_probability *= 1.0 - coverage
        else:
            # Conventional optimistic calculation: every named safeguard is
            # treated as independent even when it reads the same evidence.
            miss_probability = 1.0
            for safeguard in selected:
                miss_probability *= 1.0 - float(safeguard.coverage.get(failure_name, 0.0))
        return 1.0 - miss_probability

    def evaluate(
        self, selected: Sequence[Safeguard], *, family_aware: bool = True
    ) -> PortfolioResult:
        selected = tuple(selected)
        coverage_by_failure = {
            failure.name: self._combined_coverage(selected, failure.name, family_aware)
            for failure in self.failures
        }
        residual = sum(
            failure.probability
            * failure.consequence
            * (1.0 - coverage_by_failure[failure.name])
            for failure in self.failures
        )
        cost = sum(safeguard.cost for safeguard in selected)
        return PortfolioResult(
            safeguards=tuple(safeguard.name for safeguard in selected),
            total_cost=cost,
            expected_residual_loss=residual,
            objective=residual + cost,
            evidence_families=tuple(sorted({s.evidence_family for s in selected})),
            coverage_by_failure=coverage_by_failure,
        )

    def design(self, budget: float, *, family_aware: bool = True) -> dict[str, Any]:
        if not math.isfinite(budget) or budget < 0:
            raise ValueError("budget must be non-negative")
        feasible: list[PortfolioResult] = []
        for size in range(len(self.safeguards) + 1):
            for selected in combinations(self.safeguards, size):
                if sum(s.cost for s in selected) <= budget + 1e-12:
                    feasible.append(self.evaluate(selected, family_aware=family_aware))
        feasible.sort(key=lambda result: (result.objective, result.total_cost, result.safeguards))
        return {
            "selected": feasible[0].as_dict(),
            "top_portfolios": [result.as_dict() for result in feasible[:10]],
            "budget": budget,
            "family_aware": family_aware,
            "evaluated_portfolios": len(feasible),
        }


def designer_from_config(config: Mapping[str, Any]) -> ContractSafeguardDesigner:
    failures = [FailureMode(**item) for item in config["failure_modes"]]
    safeguards = [Safeguard(**item) for item in config["safeguards"]]
    return ContractSafeguardDesigner(failures, safeguards)
