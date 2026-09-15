from dataclasses import asdict, dataclass
import numpy as np
from .parents.mbpf import forecast_burnout_prepayment
from .parents.acsa import audit_adaptive_selection

@dataclass(frozen=True)
class BMSAResult:
    audit: dict
    truth_cumulative_prepayments: float
    status: str
    def to_dict(self): return asdict(self)

def audit_burnout_model_selection(*,cohort_size=10000,months=24,selection_months=3,holdout_start=6,bootstrap_samples=300):
    truth=forecast_burnout_prepayment(cohort_size=cohort_size,base_monthly_prepayment_rates=[.03]*months,propensity_multipliers=[.2,1,5],initial_class_weights=[.3,.4,.3])
    homogeneous=forecast_burnout_prepayment(cohort_size=cohort_size,base_monthly_prepayment_rates=[.05]*months,propensity_multipliers=[1],initial_class_weights=[1])
    burnout=forecast_burnout_prepayment(cohort_size=cohort_size,base_monthly_prepayment_rates=[.025]*months,propensity_multipliers=[.2,1,5],initial_class_weights=[.3,.4,.3])
    y=np.asarray(truth.monthly_prepayments)
    preds=[np.asarray(homogeneous.monthly_prepayments),np.asarray(burnout.monthly_prepayments)]
    s=np.column_stack([(p[:selection_months]-y[:selection_months])**2 for p in preds])
    h=np.column_stack([(p[holdout_start:]-y[holdout_start:])**2 for p in preds])
    a=audit_adaptive_selection(s,h,candidate_names=['homogeneous','burnout_aware'],bootstrap_samples=bootstrap_samples,random_seed=0,material_regret=100)
    return BMSAResult(a.to_dict(),truth.cumulative_prepayments,'BURNOUT_MODEL_SELECTION_HOLDOUT_AUDITED')
