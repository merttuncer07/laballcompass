from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np
@dataclass(frozen=True)
class Result:
    policy_effect:float|None; ess_fraction:float; min_design_eigenvalue:float; condition_number:float; status:str
    def to_dict(self): return asdict(self)

def support_constrained_policy_backaction(outcome,policy,passive_state,weights,*,min_ess_fraction=.25,min_eigenvalue=1e-4,max_condition=1e6):
    y=np.asarray(outcome,float); p=np.asarray(policy,float); s=np.asarray(passive_state,float); w=np.asarray(weights,float)
    if not (y.shape==p.shape==s.shape==w.shape) or y.ndim!=1 or len(y)<3: raise ValueError('aligned vectors with at least 3 rows required')
    if np.any(w<0) or w.sum()<=0: raise ValueError('nonnegative positive-mass weights required')
    wn=w/w.sum(); ess=1/float(np.sum(wn**2)); essf=ess/len(w)
    X=np.column_stack([np.ones(len(y)),s,p]); G=X.T@(wn[:,None]*X)
    eig=np.linalg.eigvalsh(G); mine=float(eig[0]); cond=float(np.linalg.cond(G))
    if essf<min_ess_fraction or mine<min_eigenvalue or not np.isfinite(cond) or cond>max_condition:
        return Result(None,essf,mine,cond,'SUPPORT_INADEQUATE_FOR_POLICY_BACKACTION_ESTIMATE')
    beta=np.linalg.solve(G,X.T@(wn*y))
    return Result(float(beta[2]),essf,mine,cond,'SUPPORT_CERTIFIED_POLICY_BACKACTION_ESTIMATE')
