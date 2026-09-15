from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import sys, numpy as np
_REPO=Path(__file__).resolve().parents[3]
_T=_REPO/'02_FOUNDRY_ALL_PRODUCTS'/'parent_products'/'CURRENT_PRODUCTS'/'IM178_IM326_TWMR'
if str(_T) not in sys.path: sys.path.insert(0,str(_T))
from twmr import TargetWeightedModelReducer
@dataclass(frozen=True)
class Result:
    policy_target:tuple[float,...]
    reduction:dict
    energy_baseline:dict
    relative_error_gain:float
    status:str
    def to_dict(self): return asdict(self)

def search_policy_targeted_reduction(system_matrix,input_matrix,state_names,*,policy_sensitivity,retain_count,horizon=20):
    s=np.asarray(policy_sensitivity,float)
    if s.ndim!=1 or len(s)!=len(state_names) or not np.all(np.isfinite(s)): raise ValueError('policy_sensitivity must align with state_names')
    if np.linalg.norm(s)==0: raise ValueError('nonzero policy sensitivity required')
    C=(s/np.linalg.norm(s))[None,:]
    reducer=TargetWeightedModelReducer(system_matrix,input_matrix,C,state_names)
    target=reducer.reduce(retain_count,horizon); energy=reducer.energy_baseline(retain_count,horizon)
    gain=energy.relative_target_error-target.relative_target_error
    return Result(tuple(float(x) for x in C[0]),target.as_dict(),energy.as_dict(),float(gain),'SEARCH_POLICY_TARGET_PRESERVED_DURING_REDUCTION')
