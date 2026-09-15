from dataclasses import asdict, dataclass
import numpy as np
from .parents.atrc import control_memory_retention
from .parents.acsa import audit_adaptive_selection

@dataclass(frozen=True)
class MPHAResult:
    candidate_names: tuple[str,...]
    audit: dict
    status: str
    def to_dict(self): return asdict(self)

def audit_memory_policies(selection_x,selection_y,holdout_x,holdout_y,*,policies,bootstrap_samples=300,seed=0):
    names=[]; sl=[]; hl=[]
    for name,kwargs in policies:
        a=control_memory_retention(selection_x,selection_y,seed=seed,**kwargs)
        b=control_memory_retention(holdout_x,holdout_y,seed=seed,**kwargs)
        names.append(name)
        sl.append((np.asarray(a.predictions)-np.asarray(selection_y))**2)
        hl.append((np.asarray(b.predictions)-np.asarray(holdout_y))**2)
    audit=audit_adaptive_selection(np.column_stack(sl),np.column_stack(hl),candidate_names=names,bootstrap_samples=bootstrap_samples,random_seed=seed,material_regret=.001)
    return MPHAResult(tuple(names),audit.to_dict(),'MEMORY_POLICY_HOLDOUT_AUDITED')
