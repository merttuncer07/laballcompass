from dataclasses import asdict, dataclass
from .parents.psct import discover_predictive_states
from .parents.tdsx import explore_sensitivity_surface

@dataclass(frozen=True)
class PCFTResult:
    surface: dict
    baseline_state_count: int
    baseline_compression_fraction: float
    status: str
    def to_dict(self): return asdict(self)

def predictive_closure_fidelity_tipping(sequence,*,history_length,tolerance_grid,baseline_tolerance,allowed_closure_rate,min_predictive_improvement,smoothing=.5):
    def metrics(tol):
        r=discover_predictive_states(sequence,history_length=history_length,probability_tolerance=tol,smoothing=smoothing)
        joint_margin=min(allowed_closure_rate-r.closure_violation_rate,
                         r.predictive_log_loss_improvement-min_predictive_improvement)
        return r,joint_margin
    base,_=metrics(baseline_tolerance)
    surf=explore_sensitivity_surface(lambda p:metrics(p['merge_tolerance'])[1],
        {'merge_tolerance':tolerance_grid},{'merge_tolerance':baseline_tolerance},
        decision_threshold=0.0,decision_direction='ABOVE')
    return PCFTResult(surf.to_dict(),base.predictive_state_count,base.compression_fraction,'PREDICTIVE_CLOSURE_FIDELITY_TIPPING_AUDITED')
