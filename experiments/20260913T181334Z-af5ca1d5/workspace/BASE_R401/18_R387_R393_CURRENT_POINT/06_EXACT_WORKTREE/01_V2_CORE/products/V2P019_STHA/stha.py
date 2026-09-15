from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    selected:str|None; ess_fraction:float; status:str
    def to_dict(self): return asdict(self)
def support_tipped_holdout(*,losses:dict[str,float],ess_fraction:float,support_floor:float)->Result:
    if not 0<=ess_fraction<=1 or not 0<=support_floor<=1: raise ValueError('fractions must be in [0,1]')
    if ess_fraction<support_floor:return Result(None,ess_fraction,'SUPPORT_TIP_ABORTS_HOLDOUT_SELECTION')
    if not losses:return Result(None,ess_fraction,'NO_POLICIES')
    return Result(min(losses,key=lambda k:(losses[k],k)),ess_fraction,'SUPPORTED_HOLDOUT_SELECTION')
