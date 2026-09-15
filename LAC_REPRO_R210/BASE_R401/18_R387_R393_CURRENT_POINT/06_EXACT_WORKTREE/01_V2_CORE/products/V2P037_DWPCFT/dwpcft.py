from __future__ import annotations
from dataclasses import dataclass,asdict
import math
@dataclass(frozen=True)
class Point:
    tolerance:float; consequence:float; current_samples:int; distance_to_boundary:float
@dataclass(frozen=True)
class Result:
    added_samples:dict[float,int]; before_weighted_uncertainty:float; after_weighted_uncertainty:float; uniform_after:float; status:str
    def to_dict(self): return asdict(self)

def _weight(p:Point): return max(0.,p.consequence)/(max(1e-9,abs(p.distance_to_boundary)))
def _unc(points,add): return sum(_weight(p)/math.sqrt(max(1,p.current_samples+add.get(p.tolerance,0))) for p in points)
def decision_weighted_pcft_calibration(points,*,additional_samples):
    pts=tuple(points)
    if additional_samples<0 or not pts or any(p.current_samples<0 or p.consequence<0 for p in pts): raise ValueError('valid points and nonnegative budget required')
    add={p.tolerance:0 for p in pts}
    # Greedy exact for separable diminishing marginal uncertainty reduction.
    for _ in range(additional_samples):
      best=max(pts,key=lambda p:(_weight(p)*(1/math.sqrt(max(1,p.current_samples+add[p.tolerance]))-1/math.sqrt(max(1,p.current_samples+add[p.tolerance]+1))),-p.tolerance))
      add[best.tolerance]+=1
    uniform={p.tolerance:additional_samples//len(pts) for p in pts}
    for p in pts[:additional_samples%len(pts)]:uniform[p.tolerance]+=1
    return Result(add,_unc(pts,{}),_unc(pts,add),_unc(pts,uniform),'DECISION_WEIGHTED_PCFT_CALIBRATION_ALLOCATED')
