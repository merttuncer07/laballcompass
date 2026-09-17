from __future__ import annotations
from dataclasses import dataclass,asdict
import math
@dataclass(frozen=True)
class Channel:
    name:str; immediate_value:float; cost:float; friction_after:float
@dataclass(frozen=True)
class Result:
    chosen:str|None; channel_scores:dict[str,float]; equilibria:dict[str,tuple[float,...]]; immediate_choice:str|None; status:str
    def to_dict(self): return asdict(self)

def _fixed_points(net_information,network_strength,temperature,grid=1001):
    if temperature<=0: raise ValueError('temperature must be positive')
    def F(p): return 1/(1+math.exp(-max(-60,min(60,(net_information+network_strength*p)/temperature))))
    pts=[]; lastp=0.; last=F(0)-0
    for i in range(1,grid):
      p=i/(grid-1); g=F(p)-p
      if g==0 or g*last<0:
       lo,hi=lastp,p
       for _ in range(50):
        m=(lo+hi)/2; gm=F(m)-m
        if (F(lo)-lo)*gm<=0: hi=m
        else: lo=m
       root=(lo+hi)/2
       if not pts or abs(root-pts[-1])>1e-5: pts.append(root)
      lastp,last=p,g
    return tuple(pts)

def _reachable(net_information,network_strength,temperature,start):
    p=float(start)
    for _ in range(10000):
      z=max(-60,min(60,(net_information+network_strength*p)/temperature))
      q=1/(1+math.exp(-z))
      if abs(q-p)<1e-12:return q
      p=q
    return p

def tipping_aware_information_acquisition(channels,*,base_friction,network_strength,temperature,future_opportunity_value,current_participation=0.):
    if future_opportunity_value<0 or base_friction<0: raise ValueError('nonnegative values required')
    if temperature<=0: raise ValueError('temperature must be positive')
    baseline=_reachable(-base_friction,network_strength,temperature,current_participation)
    scores={}; eq={}
    immediate={c.name:c.immediate_value-c.cost for c in channels}
    immediate_choice=max(immediate,key=immediate.get) if immediate and max(immediate.values())>0 else None
    for c in channels:
      roots=_fixed_points(c.immediate_value-c.friction_after,network_strength,temperature); eq[c.name]=roots
      p=_reachable(c.immediate_value-c.friction_after,network_strength,temperature,current_participation)
      scores[c.name]=c.immediate_value-c.cost+future_opportunity_value*(p-baseline)
    choice=max(scores,key=scores.get) if scores and max(scores.values())>0 else None
    return Result(choice,scores,eq,immediate_choice,'TIPPING_AWARE_ACQUISITION' if choice else 'NO_POSITIVE_TIPPING_ADJUSTED_CHANNEL')
