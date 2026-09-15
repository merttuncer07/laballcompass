from dataclasses import asdict, dataclass
import numpy as np
from .parents.ispo import evaluate_periodic_policy
from .parents.aicc import AdaptiveInformationController, InformationChannel

@dataclass(frozen=True)
class SPIAResult:
    policy_names: tuple[str,...]
    detection_time_vectors: tuple[tuple[float,...],...]
    current_policy: str
    chosen_channel: str|None
    ranked_channels: tuple[dict,...]
    status: str
    def to_dict(self): return asdict(self)

def _time_vector(n, local_steps, jump, **kwargs):
    out=[]
    for i in range(n):
        p=np.zeros(n); p[i]=1.0
        r=evaluate_periodic_policy(p,local_steps=local_steps,relocation_jump=jump,**kwargs)
        if not np.isfinite(r.expected_detection_time):
            raise ValueError('candidate policy must cover every declared location')
        out.append(r.expected_detection_time)
    return np.asarray(out,float)

def acquire_for_search_policy(belief_mean,belief_covariance,*,policies,channels,policy_kwargs=None):
    mean=np.asarray(belief_mean,float); cov=np.asarray(belief_covariance,float)
    if mean.ndim!=1 or np.any(mean<0) or not np.isclose(mean.sum(),1.0): raise ValueError('belief_mean must be a probability vector')
    if cov.shape!=(mean.size,mean.size): raise ValueError('covariance shape mismatch')
    if np.max(np.abs(cov.sum(axis=0)))>1e-8 or np.max(np.abs(cov.sum(axis=1)))>1e-8:
        raise ValueError('belief covariance must remain in the probability-simplex tangent space')
    for ch in channels:
        if abs(float(np.sum(ch.measurement_vector)))>1e-8: raise ValueError('measurement vectors must be zero-sum contrasts')
    kw=dict(local_observation_time=1.0,relocation_speed=10.0,relocation_overhead=.2,max_cycles=50)
    if policy_kwargs: kw.update(policy_kwargs)
    names=[]; times=[]
    for name,local,jump in policies:
        names.append(name); times.append(_time_vector(mean.size,local,jump,**kw))
    slopes=-np.vstack(times)
    ctl=AdaptiveInformationController(mean,cov,slopes,np.zeros(len(names)),list(channels))
    current=names[ctl.action()]; chosen=ctl.choose_channel(); ranked=ctl.rank_channels()
    return SPIAResult(tuple(names),tuple(tuple(map(float,t)) for t in times),current,None if chosen is None else chosen.name,tuple(asdict(x) for x in ranked),'SEARCH_POLICY_INFORMATION_ACQUISITION_COMPLETE')
