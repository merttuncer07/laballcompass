from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    choice:str|None; rejected:tuple[str,...]; status:str
    def to_dict(self): return asdict(self)
def causal_overlap_explore(*,candidates:list[tuple[str,float,float]],overlap_floor:float)->Result:
    if not 0<=overlap_floor<=1: raise ValueError('floor in [0,1]')
    good=[x for x in candidates if x[2]>=overlap_floor]
    rejected=tuple(x[0] for x in candidates if x[2]<overlap_floor)
    if not good:return Result(None,rejected,'NO_CAUSAL_OVERLAP_SUPPORTED_EXPLORATION')
    best=max(good,key=lambda x:(x[1],x[0]))
    return Result(best[0],rejected,'OVERLAP_GATED_DRE_CHOICE')
