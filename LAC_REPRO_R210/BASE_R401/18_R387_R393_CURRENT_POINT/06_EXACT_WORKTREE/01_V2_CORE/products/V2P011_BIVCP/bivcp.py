from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Sequence

@dataclass(frozen=True)
class Result:
    baseline_action: str
    baseline_loss: float
    channel: str | None
    expected_post_measurement_loss: float
    information_value: float
    channel_cost: float
    acquired: bool
    expected_total_loss: float
    status: str
    def to_dict(self): return asdict(self)

def _normalize(xs):
    s=sum(float(x) for x in xs)
    if s<=0: raise ValueError('probabilities must have positive mass')
    return [float(x)/s for x in xs]

def _loss(action, state, action_capacity, action_cost, demand, shortfall_penalty):
    return float(action_cost[action]) + float(shortfall_penalty)*max(0.0,float(demand[state])-float(action_capacity[action]))

def _best_action(probs, states, actions, action_capacity, action_cost, demand, shortfall_penalty):
    scored=[]
    for a in actions:
        v=sum(p*_loss(a,s,action_capacity,action_cost,demand,shortfall_penalty) for p,s in zip(probs,states))
        scored.append((v,str(a)))
    return min(scored)

def boundary_information_capacity_plan(*, states:Sequence[str], prior:Sequence[float], actions:Sequence[str], action_capacity:dict, action_cost:dict, demand:dict, shortfall_penalty:float, channels:dict, max_channel_cost:float=float('inf')) -> Result:
    if len(states)!=len(prior) or not states or not actions: raise ValueError('invalid state/action contract')
    probs=_normalize(prior)
    base_loss,base_action=_best_action(probs,states,actions,action_capacity,action_cost,demand,shortfall_penalty)
    best=None
    for name,ch in channels.items():
        cost=float(ch['cost'])
        if cost<0 or cost>max_channel_cost: continue
        likelihood=ch['likelihood']
        observations=list(likelihood)
        exp_post=0.0
        for obs in observations:
            ws=[probs[i]*float(likelihood[obs][states[i]]) for i in range(len(states))]
            po=sum(ws)
            if po<=0: continue
            post=[w/po for w in ws]
            post_loss,_=_best_action(post,states,actions,action_capacity,action_cost,demand,shortfall_penalty)
            exp_post += po*post_loss
        value=base_loss-exp_post
        net=value-cost
        cand=(net,-cost,str(name),exp_post,value,cost)
        if best is None or cand>best: best=cand
    if best is None or best[0] <= 0:
        return Result(base_action,base_loss,None,base_loss,0.0,0.0,False,base_loss,'NO_POSITIVE_DECISION_INFORMATION_VALUE')
    _,_,name,post,value,cost=best
    return Result(base_action,base_loss,name,post,value,cost,True,post+cost,'BOUNDARY_INFORMATION_ACQUIRED_BEFORE_CAPACITY_COMMITMENT')
