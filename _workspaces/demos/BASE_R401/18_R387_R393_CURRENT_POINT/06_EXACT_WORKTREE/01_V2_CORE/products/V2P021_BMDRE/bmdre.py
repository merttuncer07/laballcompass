from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    use_reduced:bool; tipping_distance:float; approximation_error:float; status:str
    def to_dict(self): return asdict(self)
def belief_metric_explore(*,tipping_distance:float,approximation_error:float)->Result:
    if tipping_distance<0 or approximation_error<0: raise ValueError('distances nonnegative')
    ok=approximation_error<tipping_distance
    return Result(ok,tipping_distance,approximation_error,'REDUCED_BELIEF_DECISION_SAFE' if ok else 'BELIEF_APPROXIMATION_REACHES_DECISION_TIP')
