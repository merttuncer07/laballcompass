from dataclasses import asdict, dataclass
import numpy as np
from .parents.oasrd import run_averaged_operator
from .parents.acsa import audit_adaptive_selection

@dataclass(frozen=True)
class PAOSResult:
    alpha_candidates: tuple[float,...]
    audit: dict
    status: str
    def to_dict(self): return asdict(self)

def _loss(a, alpha, iterations):
    op=lambda x: np.array([a*x[0]+1.0])
    r=run_averaged_operator(op,[0.0],alpha=alpha,maximum_iterations=iterations,residual_tolerance=0.0,divergence_norm=1e6)
    val=r.final_fixed_point_residual
    if not np.isfinite(val): val=1e6
    return min(float(val),1e6)

def audit_operator_averaging(selection_parameters,holdout_parameters,*,alphas=(1.0,.5),iterations=12,bootstrap_samples=300,seed=0):
    names=[f'alpha_{a:g}' for a in alphas]
    s=np.array([[_loss(a,alpha,iterations) for alpha in alphas] for a in selection_parameters])
    h=np.array([[_loss(a,alpha,iterations) for alpha in alphas] for a in holdout_parameters])
    audit=audit_adaptive_selection(s,h,candidate_names=names,bootstrap_samples=bootstrap_samples,random_seed=seed,material_regret=.01)
    return PAOSResult(tuple(map(float,alphas)),audit.to_dict(),'OPERATOR_AVERAGING_HOLDOUT_AUDITED')
