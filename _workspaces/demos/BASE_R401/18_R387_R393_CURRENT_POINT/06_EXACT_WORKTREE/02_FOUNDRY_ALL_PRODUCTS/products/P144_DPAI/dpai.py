from dataclasses import asdict, dataclass
import numpy as np
from .parents.dfdpe import estimate_affine_dynamics
from .parents.aicc import AdaptiveInformationController, InformationChannel

@dataclass(frozen=True)
class DPAIResult:
    persistence_estimate: float
    persistence_standard_error: float
    validation_rollout_rmse: float|None
    current_action: str
    chosen_channel: str|None
    ranked_channels: tuple[dict,...]
    status: str
    def to_dict(self): return asdict(self)

def identify_persistence_then_acquire(times,outputs,inputs,*,window_duration,window_step,channels,stability_threshold=0.0,validation=None):
    kw={}
    if validation is not None:
        kw=dict(validation_times=validation[0],validation_outputs=validation[1],validation_inputs=validation[2])
    fit=estimate_affine_dynamics(times,outputs,inputs,window_duration=window_duration,window_step=window_step,robust=True,**kw)
    if fit.estimate is None: raise RuntimeError('DFDPE did not produce an identified persistence parameter')
    est=fit.estimate; mu=np.array([est.persistence]); cov=np.array([[est.standard_errors[0]**2]])
    slopes=np.array([[-1.0],[1.0]]); intercepts=np.array([stability_threshold,-stability_threshold])
    ctl=AdaptiveInformationController(mu,cov,slopes,intercepts,list(channels))
    names=('STABLE_SIDE','UNSTABLE_SIDE'); current=names[ctl.action()]; chosen=ctl.choose_channel(); ranked=ctl.rank_channels()
    return DPAIResult(float(est.persistence),float(est.standard_errors[0]),est.validation_rollout_rmse,current,None if chosen is None else chosen.name,tuple(asdict(x) for x in ranked),'DYNAMIC_PERSISTENCE_INFORMATION_ACQUISITION_COMPLETE')
