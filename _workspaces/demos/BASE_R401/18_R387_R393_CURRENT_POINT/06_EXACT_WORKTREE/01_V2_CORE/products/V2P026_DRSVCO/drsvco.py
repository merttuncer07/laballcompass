from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    evaluate:str|None; status:str
    def to_dict(self): return asdict(self)
def decision_relevant_cycle_explore(*,points:list[tuple[str,float,float,float]],min_active:float)->Result:
    # name, estimated_product, min_active_estimate, uncertainty radius
    if not 0<=min_active<=1: raise ValueError('min_active in [0,1]')
    if not points:return Result(None,'NO_OPERATING_POINTS')
    # prioritize points whose active-state interval crosses feasibility boundary, then consequence
    crossing=[p for p in points if p[2]-p[3] < min_active <= p[2]+p[3]]
    pool=crossing if crossing else points
    best=max(pool,key=lambda p:(p[0] in [x[0] for x in crossing],p[1]*p[3],p[1],p[0]))
    return Result(best[0],'FEASIBILITY_BOUNDARY_CYCLE_EVALUATION' if crossing else 'NO_BOUNDARY_USE_HIGHEST_DECISION_LEVERAGE')
