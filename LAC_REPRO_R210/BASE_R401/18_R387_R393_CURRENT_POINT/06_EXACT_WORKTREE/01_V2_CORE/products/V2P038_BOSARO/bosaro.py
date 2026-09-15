from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np
@dataclass(frozen=True)
class Result:
    weights:tuple[float,...]; objective:float; support_radius:float; base_radius_weights:tuple[float,...]; fragile_direction_exposure:float; status:str
    def to_dict(self): return asdict(self)

def _solve(mu,d,radius,risk,step):
    n=len(mu); best=None
    if n!=2: raise ValueError('current exact grid implementation supports two actions')
    k=int(round(1/step))
    for i in range(k+1):
      w=np.array([i/k,1-i/k],float)
      obj=float(mu@w-risk*(w@w)-radius*abs(d@w))
      row=(obj,-abs(float(d@w)),tuple(w))
      if best is None or row>best:best=row
    return best

def support_aware_robust_optimizer(mean,shift_direction,*,base_shift_radius,support_fraction,risk_penalty=.01,grid_step=.002):
    mu=np.asarray(mean,float); d=np.asarray(shift_direction,float)
    if mu.shape!=d.shape or mu.ndim!=1 or len(mu)!=2: raise ValueError('aligned two-action vectors required')
    if base_shift_radius<0 or risk_penalty<0 or not 0<support_fraction<=1 or not 0<grid_step<=1: raise ValueError('invalid parameters')
    radius=base_shift_radius/(support_fraction**.5)
    robust=_solve(mu,d,radius,risk_penalty,grid_step); base=_solve(mu,d,base_shift_radius,risk_penalty,grid_step)
    w=robust[2]
    return Result(tuple(float(x) for x in w),float(robust[0]),float(radius),tuple(float(x) for x in base[2]),abs(float(d@np.array(w))),'SUPPORT_INFLATED_ADMISSIBLE_SHIFT_ROBUST_DECISION')
