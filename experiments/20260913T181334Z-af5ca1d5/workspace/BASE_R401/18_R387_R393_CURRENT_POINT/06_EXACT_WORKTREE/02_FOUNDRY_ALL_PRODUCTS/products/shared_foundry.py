"""Executable reconstruction kernel for result-only Foundry products P031-P050.

The historical package preserved claims and benchmark results but not source.  These
functions rebuild the smallest honest mechanism behind each claim.  They are not
presented as byte-identical historical code.
"""
from __future__ import annotations

from itertools import combinations, product
from math import prod
from typing import Callable, Iterable

import numpy as np


def evlt(scenarios, claims, *, audit_slots, channel_capacity, anchor_cap):
    """Exact posterior-scenario audit subset re-optimization."""
    names=tuple(sorted(claims)); best=None
    for subset in combinations(names,audit_slots):
        expected=0.
        for probability,culprits in scenarios:
            verified=sum(claims[n] for n in subset if n not in culprits)
            expected+=probability*min(verified,channel_capacity,anchor_cap)
        candidate=(expected,subset)
        if best is None or candidate>best: best=candidate
    return {'selected':best[1], 'expected_liquidity':best[0]}


def sgot(estimate,se,propensities,treatments,*,min_ess_fraction=.1,min_two_sided=.05,max_weight_share=.5):
    p=np.asarray(propensities,float); t=np.asarray(treatments,int)
    w=np.where(t==1,1/p,1/(1-p)); normalized=w/w.sum()
    ess=float(w.sum()**2/(w@w)); floor=float(np.minimum(p,1-p).min())
    deploy=ess/len(w)>=min_ess_fraction and floor>=min_two_sided and normalized.max()<=max_weight_share
    return {'estimate':estimate,'se':se,'ess':ess,'ess_fraction':ess/len(w),'max_weight_share':float(normalized.max()),'two_sided_floor':floor,'deploy':deploy,'status':'SUPPORT_USABLE' if deploy else 'SUPPORT_GATE_WITHHOLDS_DEPLOYMENT'}


def catf(regions,options,*,budget):
    """Brute-force consequence-weighted time/frequency allocation."""
    def loss(region,opt):
        return region['time_weight']*opt['time_spread']+region['frequency_weight']*opt['frequency_spread']
    feasible=[]
    for choice in product(options,repeat=len(regions)):
        cost=sum(o['cost'] for o in choice)
        if cost<=budget: feasible.append((sum(loss(r,o) for r,o in zip(regions,choice)),cost,choice))
    chosen=min(feasible,key=lambda x:(x[0],x[1]))
    fixed=[(sum(loss(r,o) for r in regions),o) for o in options if len(regions)*o['cost']<=budget]
    fixed_best=min(fixed,key=lambda x:x[0])
    return {'loss':chosen[0],'cost':chosen[1],'allocation':tuple(o['name'] for o in chosen[2]),'fixed_loss':fixed_best[0],'improvement_fraction':1-chosen[0]/fixed_best[0]}


def ugim(local_gain,ownership_path,*,control_threshold=.5):
    exposure=prod(ownership_path); controlled=all(share>control_threshold for share in ownership_path)
    return {'economic_incidence':local_gain*exposure,'exposure_fraction':exposure,'controlled':controlled,'unassigned_residual':local_gain*(1-exposure)}


def svco(couplings,*,steps,regeneration,burnout,min_active):
    rows=[]
    for coupling,static_rate in couplings.items():
        active=1.; total=0.; minimum=1.
        for _ in range(steps):
            total+=static_rate*active
            active=max(0.,min(1.,active+regeneration*(1-active)-burnout*coupling*active))
            minimum=min(minimum,active)
        rows.append({'coupling':coupling,'static_rate':static_rate,'product':total,'minimum_active':minimum,'final_active':active,'feasible':minimum>=min_active})
    feasible=[r for r in rows if r['feasible']]
    return {'static_choice':max(rows,key=lambda r:r['static_rate'])['coupling'],'stateful_choice':max(feasible,key=lambda r:r['product'])['coupling'] if feasible else None,'rows':rows}


def _validated_mass(positions, mass):
    x=np.asarray(positions,float);w=np.asarray(mass,float)
    if x.ndim!=1 or w.shape!=x.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(w)) or np.any(w<0):
        raise ValueError("positions and non-negative finite mass must be aligned vectors")
    order=np.argsort(x,kind='stable');return x[order],w[order]


def _w2_discrete(x,a,y,b):
    x,a=_validated_mass(x,a);y,b=_validated_mass(y,b)
    if a.sum()<=0 or b.sum()<=0:return None
    a=a/a.sum();b=b/b.sum();i=j=0;left=a.copy();right=b.copy();cost=0.
    while i<len(a) and j<len(b):
        moved=min(left[i],right[j]);cost+=moved*(x[i]-y[j])**2;left[i]-=moved;right[j]-=moved
        if left[i]<=1e-14:i+=1
        if right[j]<=1e-14:j+=1
    return float(max(0.,cost)**.5)


def mawt(source_positions,source_mass,target_positions,target_mass):
    sx,sw=_validated_mass(source_positions,source_mass);tx,tw=_validated_mass(target_positions,target_mass)
    sm=float(sw.sum());tm=float(tw.sum());distance=_w2_discrete(sx,sw,tx,tw)
    return {'normalized_w2':distance,'source_total':sm,'target_total':tm,'created_mass':max(0.,tm-sm),'destroyed_mass':max(0.,sm-tm),'geometry_status':'DEFINED' if distance is not None else 'UNDEFINED_ZERO_MASS','mass_semantics':'Net quantity difference; not inferred transaction-level creation/destruction.'}


def mcst(grid,violation:Callable[[float],float],*,baseline,tolerance=0.):
    failures=[(abs(x-baseline),x,violation(x)) for x in grid if violation(x)>tolerance]
    point=min(failures) if failures else None
    return {'baseline_violation':violation(baseline),'tipping_value':None if point is None else point[1],'witness_violation':None if point is None else point[2],'status':'TIPPING_POINT_FOUND' if point else 'NO_TIPPING_POINT_ON_GRID'}


def lida(normalized_power,response_rms,*,dangerous_rms,baseline_rms,scale,cap,alarm_sum,min_cycles):
    contributions=[min(cap,max(0.,(r-baseline_rms)/scale))*max(0.,p) for p,r in zip(normalized_power,response_rms)]
    count=sum(c>0 for c in contributions); cumulative=float(sum(contributions))
    return {'dangerous_windows':sum(r>=dangerous_rms for r in response_rms),'contributing_cycles':count,'cumulative_damage':cumulative,'alarm':count>=min_cycles and cumulative>=alarm_sum}


def _cycle_energy(edges):
    if not edges:return 0.
    nodes=list(dict.fromkeys(node for u,v,_ in edges for node in (u,v)));index={n:i for i,n in enumerate(nodes)}
    boundary=np.zeros((len(nodes),len(edges)));flow=np.array([v for _,_,v in edges],float)
    if not np.all(np.isfinite(flow)):raise ValueError("edge flows must be finite")
    for j,(u,v,_) in enumerate(edges):boundary[index[u],j]-=1;boundary[index[v],j]+=1
    potential=boundary.T@np.linalg.lstsq(boundary.T,flow,rcond=None)[0]
    cycle=flow-potential;energy=float(cycle@cycle)
    return 0. if energy<=1e-24*max(1.,float(flow@flow)) else energy


def cacf(edges,controlled_nodes):
    edges=list(edges);total=_cycle_energy(edges)
    inside=_cycle_energy([(u,v,f) for u,v,f in edges if u in controlled_nodes and v in controlled_nodes])
    return {'circulation_energy':total,'controlled_circulation_energy':inside,'controlled_fraction':min(1.,inside/total) if total else 0.,'semantics':'Orthogonal divergence-free flow energy; controlled energy uses the induced subgraph. Not chronological round-tripping or a fraud label.'}


def bapc(channel,receiver_utilities,prior):
    """Compute receiver decision value of a state-by-signal channel."""
    q=np.asarray(channel,float); u=np.asarray(receiver_utilities,float); prior=np.asarray(prior,float)
    value=0.
    for signal in range(q.shape[1]):
        joint=prior*q[:,signal]; value+=max(joint@u[:,action] for action in range(u.shape[1]))
    informative=not np.allclose(q,q[:,[0]]) and not np.allclose(q[0],q[1])
    return {'receiver_value':float(value),'more_informative_than_none':informative,'less_informative_than_full_revelation':not np.allclose(q,np.eye(q.shape[0]))}


def dder(max_growth,equal_diffusion_growth,current_amplitude,*,exposure_threshold,consequence_gain=1.):
    unequal=max_growth>0 and equal_diffusion_growth<=0; exposure=abs(current_amplitude*consequence_gain)
    return {'unequal_transport_instability':unequal,'exposure':exposure,'alert':unequal and exposure>=exposure_threshold}


def hpmd(model_estimates,model_weights,capacities,*,shortage_cost,excess_cost):
    names=tuple(model_estimates); best_name=max(names,key=lambda n:model_weights[n]); point=model_estimates[best_name]
    def loss(cap,total): return shortage_cost*max(0,total-cap)+excess_cost*max(0,cap-total)
    point_action=min(capacities,key=lambda c:loss(c,point))
    expected={c:sum(model_weights[n]*loss(c,model_estimates[n]) for n in names) for c in capacities}
    belief_action=min(capacities,key=expected.get)
    return {'point_action':point_action,'belief_action':belief_action,'action_inversion':point_action!=belief_action,'collapse_regret':expected[point_action]-expected[belief_action]}


def dabr(candidates,*,generic_error_budget):
    admissible=[c for c in candidates if c['error_bound']<=generic_error_budget]
    generic=min(admissible,key=lambda c:c['order']); decision=min(admissible,key=lambda c:c['protected_regret'])
    return {'generic_order':generic['order'],'decision_order':decision['order'],'generic_regret':generic['protected_regret'],'decision_regret':decision['protected_regret']}


def mfts(layer_fractions,*,thickness,min_feature):
    minimum_layer=min(layer_fractions)*thickness; margin=minimum_layer-min_feature
    return {'minimum_layer':minimum_layer,'fabrication_margin':margin,'mathematically_exact':abs(sum(layer_fractions)-1)<1e-12,'manufacturable':margin>=0}


def bdts(points,*,bottleneck_threshold,jump_threshold,baseline):
    def margin(p): return min(p['bottleneck']/bottleneck_threshold,p['jump']/jump_threshold)-1
    failures=[(abs(p['parameter']-baseline),p) for p in points if margin(p)>=0]
    point=min(failures,key=lambda x:x[0])[1] if failures else None
    return {'tipping_parameter':None if point is None else point['parameter'],'breakthrough':point is not None,'margin':None if point is None else margin(point)}


def dtrc(contracts,validation,*,shortage_cost,excess_cost):
    valid=[c for c in contracts if c['strictly_truthful']]
    def regret(c): return sum(shortage_cost*max(0,y-c['report'])+excess_cost*max(0,c['report']-y) for y in validation)/len(validation)
    chosen=min(valid,key=regret); rmse=min(valid,key=lambda c:sum((y-c['report'])**2 for y in validation))
    return {'decision_contract':chosen['name'],'prediction_contract':rmse['name'],'decision_regret':regret(chosen)}


def rala(*,lumpability_error,hidden_eigenvalue,current_exposure,recovery_steps,error_tolerance=.0,exposure_threshold=.1,recovery_limit=20):
    exact=lumpability_error<=error_tolerance; hidden_risk=abs(hidden_eigenvalue)>=.9 and current_exposure>=exposure_threshold and recovery_steps>recovery_limit
    return {'exactly_lumpable':exact,'hidden_resilience_risk':hidden_risk,'safe':exact and not hidden_risk,'status':'EXACTLY_LUMPABLE_BUT_RESILIENCE_UNSAFE' if exact and hidden_risk else 'AGGREGATION_GUARD_PASSES'}


def sara(*,structural_dimension,selected_order,error_bound):
    beyond=selected_order<structural_dimension
    return {'structural_dimension':structural_dimension,'selected_order':selected_order,'error_bound':error_bound,'status':'APPROXIMATE_IO_TRUNCATION_BEYOND_REDUNDANCY' if beyond else 'STRUCTURAL_REDUNDANCY_ONLY'}


def ogrm(transition,measurement,risky_mode,*,exposure,recovery_steps,gain_tolerance=1e-10):
    gain=float(np.linalg.norm(np.asarray(measurement)@np.asarray(risky_mode)))
    risk=exposure>0 and recovery_steps>0
    return {'measurement_gain':gain,'risk':risk,'observable':gain>gain_tolerance,'status':'CONSEQUENCE_BEARING_RESILIENCE_RISK_UNOBSERVABLE' if risk and gain<=gain_tolerance else 'RISK_OBSERVABLE'}


def cpwt(points,*,target_radius,max_volume_error,baseline):
    valid=[p for p in points if p['radius']>=target_radius and p['volume_error']<=max_volume_error]
    chosen=min(valid,key=lambda p:abs(p['parameter']-baseline)) if valid else None
    rejected=[p for p in points if p['radius']>=target_radius and p['volume_error']>max_volume_error]
    return {'selected_parameter':None if chosen is None else chosen['parameter'],'valid_target_found':chosen is not None,'conservation_rejected_parameters':tuple(p['parameter'] for p in rejected)}
