from dataclasses import asdict, dataclass
import numpy as np
from .parents.mbpf import forecast_burnout_prepayment
from .parents.ows import OverlapAwareWeightStabilizer

@dataclass(frozen=True)
class BurnoutSupportPoint:
    month: int
    class_survival_ratios: tuple[float,...]
    effective_sample_fraction: float
    max_normalized_weight: float
    support_status: str
@dataclass(frozen=True)
class BOSAResult:
    points: tuple[BurnoutSupportPoint,...]
    first_fragile_month: int|None
    naive_overprediction_fraction: float
    status: str
    def to_dict(self): return asdict(self)

def audit_burnout_support(*,cohort_size,base_rates,propensity_multipliers,initial_class_weights,months_to_audit,fragile_ess_fraction=.8,monthly_default_rates=0.0):
    f=forecast_burnout_prepayment(cohort_size=cohort_size,base_monthly_prepayment_rates=base_rates,propensity_multipliers=propensity_multipliers,initial_class_weights=initial_class_weights,monthly_default_rates=monthly_default_rates)
    initial=np.asarray(f.frailty_class_survivors[0],float)
    counts=np.rint(initial).astype(int)
    ows=OverlapAwareWeightStabilizer(fragile_ess_fraction=fragile_ess_fraction)
    pts=[]
    for m in months_to_audit:
        surv=np.asarray(f.frailty_class_survivors[m],float)
        ratios=np.divide(surv,initial,out=np.zeros_like(surv),where=initial>0)
        individual=np.concatenate([np.full(c,ratios[i]) for i,c in enumerate(counts) if c>0])
        a=ows.audit(individual)
        pts.append(BurnoutSupportPoint(int(m),tuple(map(float,ratios)),a.effective_sample_fraction,a.max_normalized_weight,a.status))
    first=next((p.month for p in pts if p.support_status=='SUPPORT_FRAGILE'),None)
    return BOSAResult(tuple(pts),first,f.naive_overprediction_fraction,'BURNOUT_SURVIVOR_SUPPORT_AUDITED')
