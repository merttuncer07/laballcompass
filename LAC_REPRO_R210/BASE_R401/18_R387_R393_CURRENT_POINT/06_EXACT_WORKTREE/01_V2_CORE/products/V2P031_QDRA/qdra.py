from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from statistics import NormalDist
import sys
_REPO=Path(__file__).resolve().parents[3]
_A=_REPO/'02_FOUNDRY_ALL_PRODUCTS'/'parent_products'/'CURRENT_PRODUCTS'/'IM406_IM037_ACRA'
if str(_A) not in sys.path: sys.path.insert(0,str(_A))
from acra import DecisionRegion,ResolutionOption,AdaptiveConsequenceResolutionAllocator

@dataclass(frozen=True)
class ValidityRegion:
    name:str; mean:float; variance:float; threshold:float; consequence:float; time_importance:float=1.; frequency_importance:float=1.
@dataclass(frozen=True)
class Result:
    allocation:dict
    decision_weights:dict[str,float]
    status:str
    def to_dict(self): return asdict(self)

def _boundary_mass(mean,var,threshold,noise):
    sd=(max(0.,var)+max(0.,noise)**2)**.5
    if sd==0:return float(abs(mean-threshold)<1e-15)
    z=abs(mean-threshold)/sd
    return 2*(1-NormalDist().cdf(z))

def quasineutral_decision_resolution(regions,options,*,budget):
    if not regions: raise ValueError('regions required')
    # Information matters only where measurement uncertainty can flip the validity decision.
    # Current belief mass near the decision boundary. Resolution options then compete
    # for that decision-relevant consequence inside ACRA.
    weights={r.name:r.consequence*_boundary_mass(r.mean,r.variance,r.threshold,0.0) for r in regions}
    ar=[DecisionRegion(r.name,r.time_importance,r.frequency_importance,weights[r.name]) for r in regions]
    result=AdaptiveConsequenceResolutionAllocator(ar,options).allocate(budget)
    return Result(result,weights,'DECISION_BOUNDARY_WEIGHTED_RESOLUTION_ALLOCATED')
