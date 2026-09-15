from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    representation:str; fidelity:float; status:str
    def to_dict(self): return asdict(self)
def closure_fidelity_explore(*,fidelity:float,floor:float)->Result:
    if not 0<=fidelity<=1 or not 0<=floor<=1: raise ValueError('fidelity in [0,1]')
    ok=fidelity>=floor
    return Result('reduced' if ok else 'full',fidelity,'PREDICTIVE_CLOSURE_SUPPORTS_REDUCED_DRE' if ok else 'CLOSURE_FIDELITY_TIP_FORCES_FULL_DRE')
