from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Sequence

@dataclass(frozen=True)
class Item:
    name:str
    nominal_value:float
    pool_contributions:tuple[float,...]
    support_fraction:float

@dataclass(frozen=True)
class Result:
    allocation:dict[str,float]
    supported_value:float
    nominal_value:float
    excluded:tuple[str,...]
    order:tuple[str,...]
    status:str
    def to_dict(self): return asdict(self)

def _rank(items:Sequence[Item], caps:Sequence[float], subset:Sequence[int])->float:
    return sum(min(float(caps[p]),sum(items[i].pool_contributions[p] for i in subset)) for p in range(len(caps)))

def support_adjusted_shared_capacity(items:Sequence[Item], pool_capacities:Sequence[float], *, min_support:float=.25)->Result:
    items=tuple(items); caps=tuple(float(x) for x in pool_capacities)
    if not items or not caps: raise ValueError('nonempty items and capacities required')
    if any(x<0 for x in caps): raise ValueError('capacities must be nonnegative')
    if not 0<=min_support<=1: raise ValueError('min_support must lie in [0,1]')
    for x in items:
        if len(x.pool_contributions)!=len(caps) or any(v<0 for v in x.pool_contributions): raise ValueError('aligned nonnegative pool contributions required')
        if x.nominal_value<0 or not 0<=x.support_fraction<=1: raise ValueError('nonnegative value and support in [0,1] required')
    eligible=[i for i,x in enumerate(items) if x.support_fraction>=min_support]
    excluded=tuple(x.name for x in items if x.support_fraction<min_support)
    adjusted={i:items[i].nominal_value*items[i].support_fraction for i in eligible}
    order=sorted(eligible,key=lambda i:(-adjusted[i],items[i].name))
    chosen=[]; prev=0.; alloc={x.name:0. for x in items}
    for i in order:
        chosen.append(i); cur=_rank(items,caps,chosen); alloc[items[i].name]=cur-prev; prev=cur
    supported=sum(adjusted[i]*alloc[items[i].name] for i in eligible)
    nominal=sum(items[i].nominal_value*alloc[items[i].name] for i in eligible)
    return Result(alloc,float(supported),float(nominal),excluded,tuple(items[i].name for i in order),'SUPPORT_ADJUSTED_POLYMATROID_ALLOCATION')
