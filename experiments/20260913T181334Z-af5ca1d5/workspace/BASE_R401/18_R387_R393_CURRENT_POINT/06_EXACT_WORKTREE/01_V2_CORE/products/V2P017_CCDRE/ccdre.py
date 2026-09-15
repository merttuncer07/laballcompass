from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    choice:str|None; blocked:tuple[str,...]; status:str
    def to_dict(self): return asdict(self)
def conservation_calibrated_explore(*,channels:list[tuple[str,float,float]],residual_limit:float)->Result:
    if residual_limit<0: raise ValueError('limit must be nonnegative')
    good=[x for x in channels if abs(x[2])<=residual_limit]
    blocked=tuple(n for n,_,r in channels if abs(r)>residual_limit)
    if not good:return Result(None,blocked,'NO_CONSERVATION_ADMISSIBLE_CHANNEL')
    best=max(good,key=lambda x:(x[1],x[0]))
    return Result(best[0],blocked,'CONSERVATION_FILTERED_DRE_CHOICE')
