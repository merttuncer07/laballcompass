from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    choice:str|None; distance:float|None; status:str
    def to_dict(self): return asdict(self)
def wasserstein_tipped_explore(*,candidates:list[tuple[str,float,float]],max_distance:float)->Result:
    if max_distance<0: raise ValueError('max distance must be nonnegative')
    feasible=[x for x in candidates if 0<=x[1]<=max_distance and x[2]>0]
    if not feasible:return Result(None,None,'NO_NEARBY_DECISION_TIP')
    best=min(feasible,key=lambda x:(x[1]/x[2],x[1],x[0]))
    return Result(best[0],best[1],'WASSERSTEIN_TIP_PRIORITIZED_EXPLORATION')
