import numpy as np
from .mpha import *

def streams():
    rng=np.random.default_rng(0)
    n=80
    # Selection stream: fast-moving one-way regime. Short memory looks best.
    xs=np.arange(n)[:,None].astype(float)
    ys=np.sin(np.arange(n)/3)+rng.normal(0,.05,n)
    # Untouched holdout: repeating states. Long memory can reuse prior matching states.
    xh=(np.arange(n)%10)[:,None].astype(float)
    yh=np.sin((np.arange(n)%10)/2)+rng.normal(0,.05,n)
    return xs,ys,xh,yh
P=[('short',dict(memory_budget=4,audit_horizon=4,neighbors=1,age_penalty=.02)),('long',dict(memory_budget=14,audit_horizon=12,neighbors=3,age_penalty=0.0))]

def result():
    x,y,xh,yh=streams(); return audit_memory_policies(x,y,xh,yh,policies=P,bootstrap_samples=400,seed=0)

def test_selection_prefers_short():
    r=result(); assert r.audit['selected_candidate']=='short'
def test_holdout_prefers_long():
    r=result(); assert r.audit['holdout_best_candidate']=='long'
def test_material_regret_detected():
    r=result(); assert r.audit['selected_holdout_regret']>.05; assert r.audit['status']=='ADAPTIVE_SELECTION_REGRET_DETECTED'
def test_holdout_gap_is_large():
    r=result(); losses=dict(zip(r.candidate_names,r.audit['holdout_mean_losses'])); assert losses['short']>3*losses['long']
def test_candidate_columns_match():
    r=result(); assert len(r.audit['selection_mean_losses'])==2
def test_status_contract():
    assert result().status=='MEMORY_POLICY_HOLDOUT_AUDITED'
