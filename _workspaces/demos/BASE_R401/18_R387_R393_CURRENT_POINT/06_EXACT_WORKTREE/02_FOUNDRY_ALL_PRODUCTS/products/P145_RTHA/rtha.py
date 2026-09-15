from dataclasses import asdict, dataclass
import numpy as np
from .parents.rto import evaluate_restart_threshold
from .parents.acsa import audit_adaptive_selection

@dataclass(frozen=True)
class RTHAResult:
    candidate_names: tuple[str,...]
    audit: dict
    status: str
    def to_dict(self): return asdict(self)

def _name(t): return 'no_restart' if t is None else f'threshold_{float(t):g}'
def audit_restart_thresholds(selection_batches,holdout_batches,*,thresholds,restart_overhead=0.0,bootstrap_samples=300):
    names=tuple(_name(t) for t in thresholds)
    def matrix(batches):
        return np.asarray([[evaluate_restart_threshold(np.asarray(batch,float),t,restart_overhead).expected_completion_time for t in thresholds] for batch in batches],float)
    s=matrix(selection_batches); h=matrix(holdout_batches)
    finite_cap=max(np.max(s[np.isfinite(s)],initial=1),np.max(h[np.isfinite(h)],initial=1))*100
    s=np.where(np.isfinite(s),s,finite_cap); h=np.where(np.isfinite(h),h,finite_cap)
    a=audit_adaptive_selection(s,h,candidate_names=names,bootstrap_samples=bootstrap_samples,random_seed=0,material_regret=.1)
    return RTHAResult(names,a.to_dict(),'RESTART_THRESHOLD_HOLDOUT_AUDITED')
