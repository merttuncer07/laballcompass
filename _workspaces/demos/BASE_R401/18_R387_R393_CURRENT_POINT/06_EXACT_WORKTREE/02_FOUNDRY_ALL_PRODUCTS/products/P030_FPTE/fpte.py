from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FailureMechanism:
    name: str
    activation_threshold: float
    full_energy: float


@dataclass(frozen=True)
class FailurePathTippingResult:
    baseline_energy: float
    required_energy: float
    tipping_retention: float | None
    tipping_energy: float | None
    activated_at_tipping: tuple[str, ...]
    status: str


def frozen_architecture_energy(mechanisms: list[FailureMechanism], retention: float) -> tuple[float,tuple[str,...]]:
    remaining=retention; energy=0.; active=[]
    for mechanism in mechanisms:
        if remaining+1e-12 < mechanism.activation_threshold: break
        active.append(mechanism.name); energy += mechanism.full_energy*remaining; remaining*=retention
    return energy,tuple(active)


def explore_retention_tipping(mechanisms: list[FailureMechanism], *, baseline_retention: float, retention_grid: list[float], required_energy: float) -> FailurePathTippingResult:
    baseline,_=frozen_architecture_energy(mechanisms,baseline_retention)
    failures=[]
    for r in retention_grid:
        energy,active=frozen_architecture_energy(mechanisms,r)
        if energy<required_energy: failures.append((abs(r-baseline_retention),r,energy,active))
    if not failures: return FailurePathTippingResult(baseline,required_energy,None,None,(), 'NO_FAILURE_TIPPING_POINT_ON_GRID')
    _,r,e,a=min(failures)
    return FailurePathTippingResult(baseline,required_energy,r,e,a,'FROZEN_ARCHITECTURE_FAILURE_TIPPING_FOUND')
