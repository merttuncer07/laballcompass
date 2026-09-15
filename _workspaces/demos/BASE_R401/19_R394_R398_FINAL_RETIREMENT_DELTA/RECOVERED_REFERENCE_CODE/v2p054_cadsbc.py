"""Reference reconstruction of V2P054 CADSBC.
Not canonical bytes. Mechanism: consequence-adaptive representation allocation before DSBC compression.
"""
from dataclasses import dataclass
from typing import Sequence
import math

@dataclass(frozen=True)
class Allocation:
    modes: tuple[str,...]
    state_cost: int
    weighted_regret: float

_MODE_COST={'coarse':1,'balanced':2,'fine':3}
_MODE_REGRET={'coarse':1.0,'balanced':0.55,'fine':0.20}

def consequence_adaptive_modes(consequence: Sequence[float], budget:int)->tuple[str,...]:
    if not consequence or any(not math.isfinite(float(x)) or x<0 for x in consequence): raise ValueError('finite non-negative consequences required')
    if not isinstance(budget,int) or budget < len(consequence): raise ValueError('budget too small or not an integer')
    n=len(consequence); modes=['coarse']*n; left=budget-n
    c=[float(x) for x in consequence]
    # Greedy marginal consequence-weighted regret reduction per unit state cost.
    while left>0:
        candidates=[]
        for i,m in enumerate(modes):
            nxt='balanced' if m=='coarse' else ('fine' if m=='balanced' else None)
            if nxt is None: continue
            gain=c[i]*(_MODE_REGRET[m]-_MODE_REGRET[nxt])
            candidates.append((gain,-i,i,nxt))
        if not candidates: break
        _,_,i,nxt=max(candidates)
        modes[i]=nxt; left-=1
    return tuple(modes)

def evaluate(consequence:Sequence[float], modes:Sequence[str])->Allocation:
    c=[float(x) for x in consequence]
    if len(c)!=len(modes): raise ValueError('alignment')
    regret=sum(ci*_MODE_REGRET[m] for ci,m in zip(c,modes))
    return Allocation(tuple(modes),sum(_MODE_COST[m] for m in modes),regret)

def candidate(consequence:Sequence[float],budget:int)->Allocation:
    return evaluate(consequence, consequence_adaptive_modes(consequence,budget))

def removal_control(consequence:Sequence[float],budget:int)->Allocation:
    consequence_adaptive_modes(consequence,budget)
    n=len(consequence); base=budget//n
    mode='balanced' if base>=2 else 'coarse'
    return evaluate(consequence,(mode,)*n)
