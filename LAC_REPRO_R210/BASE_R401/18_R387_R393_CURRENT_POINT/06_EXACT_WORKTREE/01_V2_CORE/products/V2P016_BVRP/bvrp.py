from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    action:str; boundary_crossed:bool; fallback_used:bool; status:str
    def to_dict(self): return asdict(self)
def boundary_viability_plan(*,lower_action:str,upper_action:str,nominal_action:str,safe_fallback:str)->Result:
    if not nominal_action or not safe_fallback: raise ValueError('actions required')
    crossed=lower_action!=upper_action
    return Result(safe_fallback if crossed else nominal_action,crossed,crossed,'BOUNDARY_TRIGGERED_VIABILITY_FALLBACK' if crossed else 'ACTION_INVARIANT_NOMINAL_PLAN')
