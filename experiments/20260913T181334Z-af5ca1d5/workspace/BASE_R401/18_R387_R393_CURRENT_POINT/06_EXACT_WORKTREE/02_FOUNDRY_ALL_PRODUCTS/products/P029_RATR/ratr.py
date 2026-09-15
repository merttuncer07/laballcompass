from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReductionCandidate:
    retained: tuple[str, ...]
    target_error: float
    resilience_alert: bool


@dataclass(frozen=True)
class ResilienceAwareReduction:
    selected: ReductionCandidate | None
    reference_alert: bool
    refused: bool
    status: str


def select_resilience_aware_reduction(candidates: list[ReductionCandidate], *, reference_alert: bool, state_budget: int) -> ResilienceAwareReduction:
    feasible=[c for c in candidates if len(c.retained)<=state_budget and c.resilience_alert==reference_alert]
    if not feasible: return ResilienceAwareReduction(None,reference_alert,True,'NO_REDUCTION_PRESERVES_CURRENT_RESILIENCE_STATUS')
    selected=min(feasible,key=lambda c:(c.target_error,len(c.retained),c.retained))
    return ResilienceAwareReduction(selected,reference_alert,False,'RESILIENCE_STATUS_PRESERVING_REDUCTION_FOUND')
