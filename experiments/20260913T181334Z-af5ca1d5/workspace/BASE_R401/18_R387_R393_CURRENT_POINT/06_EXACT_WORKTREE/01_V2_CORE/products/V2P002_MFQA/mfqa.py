from __future__ import annotations

from dataclasses import asdict,dataclass
from math import floor

import numpy as np
from numpy.polynomial.hermite import hermgauss


@dataclass(frozen=True)
class FidelityChannel:
    name:str
    noise_variance:float
    cost:float


@dataclass(frozen=True)
class MFQAResult:
    current_imbalance:float
    distance_to_tolerance:float
    fine_net_value:float
    cheap_net_value:float
    mode:str
    n_fine:int
    n_cheap:int
    spent_budget:float
    variance_proxy:float|None
    status:str
    def to_dict(self):return asdict(self)


def _decision_improvement(mu,var,noise,tolerance,quadrature_points=41):
    if var<0 or noise<=0:raise ValueError('variance and noise must be valid')
    current=max(tolerance-mu,mu-tolerance)
    predictive=var+noise
    gain=var/predictive
    nodes,weights=hermgauss(quadrature_points);weights=weights/np.sqrt(np.pi)
    posterior=0.
    for node,weight in zip(nodes,weights):
        residual=np.sqrt(2*predictive)*node; post_mu=mu+gain*residual
        posterior+=float(weight)*max(tolerance-post_mu,post_mu-tolerance)
    return max(0.,posterior-current)


def _lcb_allocation(total_budget,fine_cost,cheap_cost,rho,min_fine):
    C=float(total_budget);rh=min(abs(float(rho)),.999)
    max_fine=int(C//fine_cost)
    best={'mode':'fine_only','n_fine':max_fine,'n_cheap':0,'variance_proxy':1/max(max_fine,1)}
    for nf in range(int(min_fine),max_fine+1):
        nc=int((C-fine_cost*nf)//cheap_cost)
        if nc<nf:continue
        variance=(1-rh*rh)/nf+(rh*rh)/nc
        if variance<best['variance_proxy']:
            best={'mode':'multifidelity','n_fine':nf,'n_cheap':nc,'variance_proxy':variance}
    return best


def allocate_quasineutral_measurements(imbalance,belief_variance,*,tolerance,total_budget,fine_channel,cheap_channel,pilot_correlation,min_fine=4,min_correlation=.2):
    """QAIG decision-value gate followed by LCB multi-fidelity budget allocation."""
    if total_budget<0 or fine_channel.cost<=0 or cheap_channel.cost<=0 or min_fine<1:raise ValueError('invalid budget/channel contract')
    fine_improvement=_decision_improvement(imbalance,belief_variance,fine_channel.noise_variance,tolerance)
    cheap_improvement=_decision_improvement(imbalance,belief_variance,cheap_channel.noise_variance,tolerance)
    fine_net=fine_improvement-fine_channel.cost;cheap_net=cheap_improvement-cheap_channel.cost
    if max(fine_net,cheap_net)<=0 or total_budget<min(fine_channel.cost,cheap_channel.cost):
        return MFQAResult(imbalance,abs(imbalance-tolerance),fine_net,cheap_net,'no_measurement',0,0,0,None,'VALIDITY_DECISION_VALUE_DOES_NOT_JUSTIFY_MEASUREMENT')
    baseline_count=int(total_budget//fine_channel.cost)
    if fine_net<=0:
        cheap_count=int(total_budget//cheap_channel.cost)
        return MFQAResult(imbalance,abs(imbalance-tolerance),fine_net,cheap_net,'cheap_only',0,cheap_count,cheap_count*cheap_channel.cost,1/max(cheap_count,1),'CHEAP_CHANNEL_ONLY_HAS_POSITIVE_DECISION_VALUE')
    proposal=_lcb_allocation(total_budget,fine_channel.cost,cheap_channel.cost,pilot_correlation,min_fine)
    allow_multi=cheap_net>0 and abs(pilot_correlation)>=min_correlation and proposal['mode']=='multifidelity'
    if allow_multi:
        nf,nc=proposal['n_fine'],proposal['n_cheap'];mode='multifidelity'
        status='DECISION_GATED_MULTIFIDELITY_PROGRAM_ALLOCATED'
    else:
        nf,nc=baseline_count,0;mode='fine_only'
        status='FINE_ONLY_ROUTER_USED_CHEAP_CHANNEL_NOT_QUALIFIED'
    spent=nf*fine_channel.cost+nc*cheap_channel.cost
    return MFQAResult(imbalance,abs(imbalance-tolerance),fine_net,cheap_net,mode,nf,nc,spent,proposal['variance_proxy'] if allow_multi else 1/max(nf,1),status)
