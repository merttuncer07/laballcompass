"""Callable replacements for lost historical sources, with explicit input contracts.

These generic shells are not implementations of the parent mechanisms named in
historical metadata. Outputs retain that source-fidelity boundary.
"""
from __future__ import annotations
import math


def number(record,key,fallback=None,default=None):
    value=record.get(key,record.get(fallback,default) if fallback else default)
    if value is None:raise ValueError(f"Missing numeric field: {key}")
    value=float(value)
    if not math.isfinite(value):raise ValueError(f"{key} must be finite")
    return value


def evaluate_spec_product(spec,records,*,baseline=None,budget=None):
    records=list(records)
    if not records:raise ValueError('records cannot be empty')
    names=[r.get('name') for r in records]
    if any(not isinstance(n,str) or not n for n in names) or len(set(names))!=len(names):raise ValueError('record names must be nonempty and unique')
    mode=spec['execution_mode']
    if mode=='tipping':
        if baseline is None or not isinstance(baseline.get('decision'),bool):raise ValueError('tipping requires a baseline with a boolean decision')
        origin=number(baseline,'parameter')
        for r in records:
            number(r,'parameter')
            if not isinstance(r.get('decision'),bool):raise ValueError('tipping records require a boolean decision')
        flipped=[r for r in records if r['decision']!=baseline['decision']]
        chosen=min(flipped,key=lambda r:abs(number(r,'parameter')-origin)) if flipped else None
        payload={'tipping_record':chosen,'status':'TIPPING_FOUND' if chosen else 'NO_TIPPING_ON_DECLARED_GRID'}
    elif mode=='audit':
        # Protected observations cannot be silently substituted with selection scores.
        for r in records:number(r,'selection_score','score');number(r,'protected_score')
        selected=max(records,key=lambda r:number(r,'selection_score','score'))
        protected=max(records,key=lambda r:number(r,'protected_score'))
        regret=number(protected,'protected_score')-number(selected,'protected_score')
        payload={'selected':selected['name'],'protected_best':protected['name'],'protected_regret':regret,'status':'PROTECTED_FAILURE_DETECTED' if regret>0 else 'PROTECTED_SURVIVAL'}
    elif mode=='allocation':
        if budget is None or not math.isfinite(float(budget)) or budget<0:raise ValueError('allocation requires a finite non-negative budget')
        # Dominance-pruned 0/1 knapsack frontier. No rounding of costs or reuse of items.
        frontier=[(0.,0.,())]
        for i,r in enumerate(records):
            cost=number(r,'cost',default=1);value=number(r,'value','score')
            if cost<0:raise ValueError('cost must be non-negative')
            candidates=frontier+[(c+cost,v+value,chosen+(i,)) for c,v,chosen in frontier if c+cost<=budget]
            candidates.sort(key=lambda x:(x[0],-x[1],x[2]))
            frontier=[];best=-math.inf
            for state in candidates:
                if state[1]>best:frontier.append(state);best=state[1]
            if len(frontier)>100000:raise ValueError('Exact allocation frontier exceeds 100,000 states; split the problem or use a specialized solver')
        cost,value,chosen=max(frontier,key=lambda x:(x[1],-x[0]))
        payload={'selected':tuple(records[i]['name'] for i in chosen),'total_value':value,'total_cost':cost,'status':'BUDGETED_ALLOCATION_COMPLETE'}
    elif mode in ('selection','feasibility'):
        for r in records:
            number(r,'score','value')
            if not isinstance(r.get('feasible',True),bool) or not isinstance(r.get('gate',True),bool):raise ValueError('feasible and gate must be boolean')
        feasible=[r for r in records if r.get('feasible',True) and r.get('gate',True)]
        chosen=max(feasible,key=lambda r:number(r,'score','value')) if feasible else None
        payload={'selected':None if chosen is None else chosen['name'],'status':'COMPOSITION_SELECTED' if chosen else 'NO_FEASIBLE_COMPOSITION'}
    else:raise ValueError('Unknown execution mode: '+str(mode))
    return {'product_id':spec['product_id'],'short_name':spec['short_name'],'reconstruction_tier':spec.get('reconstruction_tier','SPEC_EXECUTABLE_NOT_HISTORICAL_SOURCE'),'execution_mode':mode,**payload}
