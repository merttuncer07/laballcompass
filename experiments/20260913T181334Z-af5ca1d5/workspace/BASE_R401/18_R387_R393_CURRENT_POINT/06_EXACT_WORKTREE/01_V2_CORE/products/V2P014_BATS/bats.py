from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    boundary_crossed: bool; selected_time: float|None; spent: float; status: str
    def to_dict(self): return asdict(self)
def boundary_aware_timing(*, lower_action:int, upper_action:int, timing_candidates:list[tuple[float,float]], budget:float)->Result:
    if budget<0: raise ValueError("budget must be nonnegative")
    if any(c<0 for _,c in timing_candidates): raise ValueError("cost must be nonnegative")
    crossed=lower_action!=upper_action
    if not crossed: return Result(False,None,0.0,'ACTION_INVARIANT_SKIP_TIMING')
    feasible=[x for x in timing_candidates if x[1]<=budget]
    if not feasible: return Result(True,None,0.0,'BOUNDARY_PRESENT_NO_AFFORDABLE_TIMING')
    t,c=min(feasible,key=lambda x:(x[1],x[0]))
    return Result(True,float(t),float(c),'BOUNDARY_GATED_TIMING_ACQUIRED')
