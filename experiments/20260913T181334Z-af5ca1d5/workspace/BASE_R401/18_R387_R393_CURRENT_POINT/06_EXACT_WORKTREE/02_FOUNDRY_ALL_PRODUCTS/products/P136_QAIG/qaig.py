from dataclasses import asdict, dataclass
import numpy as np
from .parents.aptc import calculate_ambipolar_transport
from .parents.aicc import AdaptiveInformationController, InformationChannel

@dataclass(frozen=True)
class QAIGResult:
    imbalance: float
    transport_status: str
    chosen_channel: str|None
    ranked_channels: tuple[dict,...]
    status: str
    def to_dict(self): return asdict(self)

def gate_quasineutral_measurement(positions,electron_density,hole_density,*,transport_kwargs,belief_variance,channels,tolerance=.05):
    tr=calculate_ambipolar_transport(positions,electron_density,hole_density,quasineutrality_tolerance=tolerance,**transport_kwargs)
    mu=np.array([tr.maximum_relative_charge_imbalance])
    ctl=AdaptiveInformationController(mu,np.array([[belief_variance]]),np.array([[-1.0],[1.0]]),np.array([tolerance,-tolerance]),channels)
    ranked=ctl.rank_channels(); ch=ctl.choose_channel()
    return QAIGResult(float(mu[0]),tr.status,None if ch is None else ch.name,tuple(asdict(x) for x in ranked),'MEASURE_IF_VALIDITY_BOUNDARY_VALUE_POSITIVE')
