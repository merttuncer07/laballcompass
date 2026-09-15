from __future__ import annotations
from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class Result:
    ess_fraction: float
    nominal_sigma: float
    effective_sigma: float
    nominal_reserve: float
    support_adjusted_reserve: float
    support_fragile: bool
    status: str
    def to_dict(self): return asdict(self)

def support_adjusted_reserve(*, mean_demand:float, nominal_sigma:float, ess_fraction:float, z:float=1.645, fragile_floor:float=0.8, max_inflation:float=4.0)->Result:
    if nominal_sigma<0 or mean_demand<0: raise ValueError('nonnegative demand/sigma required')
    if not (0 < ess_fraction <= 1): raise ValueError('ess_fraction must be in (0,1]')
    if not (0 < fragile_floor <= 1) or max_inflation < 1: raise ValueError('invalid support contract')
    nominal=float(mean_demand)+float(z)*float(nominal_sigma)
    fragile=ess_fraction < fragile_floor
    inflation=min(max_inflation,1.0/math.sqrt(float(ess_fraction))) if fragile else 1.0
    eff=float(nominal_sigma)*inflation
    adjusted=float(mean_demand)+float(z)*eff
    return Result(float(ess_fraction),float(nominal_sigma),eff,nominal,adjusted,fragile,'SUPPORT_FRAGILITY_INFLATES_CAPACITY_UNCERTAINTY' if fragile else 'SUPPORT_USABLE_NOMINAL_CAPACITY_PLAN')

def realized_shortfall(reserve:float, realized_demand:float)->float:
    return max(0.0,float(realized_demand)-float(reserve))
