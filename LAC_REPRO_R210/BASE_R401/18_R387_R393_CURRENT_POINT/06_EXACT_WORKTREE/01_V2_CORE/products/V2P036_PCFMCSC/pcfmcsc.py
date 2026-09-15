from __future__ import annotations
from dataclasses import dataclass,asdict
@dataclass(frozen=True)
class Result:
    monotone_safe:bool; first_violation:tuple|None; safe_intervals:tuple[tuple[float,float],...]; status:str
    def to_dict(self): return asdict(self)

def closure_fidelity_monotonicity(tolerances,joint_margins,*,expected_direction='NONINCREASING'):
    x=list(map(float,tolerances)); y=list(map(float,joint_margins))
    if len(x)!=len(y) or len(x)<2 or any(x[i]>=x[i+1] for i in range(len(x)-1)): raise ValueError('strictly increasing aligned grid required')
    if expected_direction not in {'NONINCREASING','NONDECREASING'}: raise ValueError('bad direction')
    bad=None
    for i in range(len(y)-1):
      violation=(y[i+1]>y[i]+1e-12) if expected_direction=='NONINCREASING' else (y[i+1]<y[i]-1e-12)
      if violation: bad=(x[i],x[i+1],y[i],y[i+1]); break
    intervals=[]; start=None
    for i,(xx,yy) in enumerate(zip(x,y)):
      if yy>=0 and start is None:start=xx
      if (yy<0 or i==len(y)-1) and start is not None:
       end=x[i-1] if yy<0 else xx; intervals.append((start,end)); start=None
    return Result(bad is None,bad,tuple(intervals),'CLOSURE_FIDELITY_DIRECTION_CERTIFIED' if bad is None else 'NONMONOTONE_CLOSURE_FIDELITY_WITNESS')
