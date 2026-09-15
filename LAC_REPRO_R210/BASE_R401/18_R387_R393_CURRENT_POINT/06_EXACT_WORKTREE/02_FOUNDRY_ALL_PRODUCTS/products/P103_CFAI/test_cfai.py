from itertools import product
import math
import numpy as np
import pytest
from .cfai import allocate_flow_review, evaluate, PRODUCT_SPEC


def config():
    return {'node_count':4,'edges':[[0,1],[1,2],[2,0],[2,3]],
            'base_flows':[[10.,10.,10.,1000.]],'budget':1.,
            'edge_names':['cycle_a','cycle_b','cycle_c','large_bridge']}


def test_native_composition_uses_graph_not_supplied_priority_scores():
    r=evaluate(config())
    assert r['reconstruction_tier']=='NATIVE_REIMPLEMENTATION_NOT_HISTORICAL_SOURCE'
    assert {m['name'] for m in r['mechanisms']}=={'HFAD','BICC','ACRA'}
    assert r['baseline_cycle_energy'][0]==pytest.approx(300.)
    priority={x['edge_name']:x for x in r['edge_priority']}
    assert priority['cycle_a']['rms_energy_change']==pytest.approx(500./3.)
    assert priority['large_bridge']['rms_energy_change'] < 1e-8
    selected=[x['edge_name'] for x in r['plan']['allocations'] if x['option']=='reviewed']
    assert len(selected)==1 and selected[0]!='large_bridge'
    assert r['probabilistic_certificate'] is None
    assert r['influence_scope']=='EMPIRICAL_SCENARIO_INFLUENCE'


def test_same_flow_values_on_a_tree_have_no_circulation_signal():
    c=config();c['node_count']=5;c['edges']=[[0,1],[1,2],[2,3],[3,4]]
    r=evaluate(c)
    assert max(r['baseline_cycle_energy']) < 1e-16
    assert max(x['rms_energy_change'] for x in r['edge_priority']) < 1e-16


def test_allocation_matches_independent_exhaustive_budget_oracle():
    c=config();c['budget']=2.5
    c['replacement_flows']=[[0.,9.,9.5,0.]]
    c['options']=[{'name':'coarse','cost':0.,'residual_error':1.},
                  {'name':'medium','cost':.75,'residual_error':.4},
                  {'name':'fine','cost':2.,'residual_error':.05}]
    r=evaluate(c)
    effects={p['edge_name']:p['rms_energy_change'] for p in r['edge_priority']}
    losses=[]
    for choices in product(c['options'],repeat=4):
        if sum(o['cost'] for o in choices)<=c['budget']+1e-12:
            losses.append(sum((effects[name]*o['residual_error'])**2 for name,o in zip(c['edge_names'],choices)))
    assert r['plan']['remaining_influence_score']==pytest.approx(min(losses))
    assert r['plan']['total_cost']<=c['budget']


def test_custom_replacement_changes_which_edge_receives_resolution():
    c=config();c['replacement_flows']=[[9.9,0.,9.9,0.]]
    r=evaluate(c)
    assert next(a['edge_name'] for a in r['plan']['allocations'] if a['option']=='reviewed')=='cycle_b'


def test_permuting_edges_preserves_priorities_and_objective():
    c=config();r=evaluate(c);perm=[3,1,0,2]
    c['edges']=[c['edges'][i] for i in perm]
    c['edge_names']=[c['edge_names'][i] for i in perm]
    c['base_flows']=[[c['base_flows'][0][i] for i in perm]]
    p=evaluate(c)
    assert {x['edge_name']:x['rms_energy_change'] for x in p['edge_priority']}==pytest.approx({x['edge_name']:x['rms_energy_change'] for x in r['edge_priority']},abs=1e-8)
    assert p['plan']['remaining_influence_score']==pytest.approx(r['plan']['remaining_influence_score'])


def test_score_only_placeholder_inputs_no_longer_fake_native_execution():
    with pytest.raises(ValueError,match='graph configuration'):evaluate([{'name':'a','score':100}])
    with pytest.raises(ValueError):evaluate({})


def test_invalid_flow_resolution_and_budget_rejected():
    c=config();c['base_flows']=[[1.,2.]]
    with pytest.raises(ValueError):evaluate(c)
    c=config();c['budget']=float('nan')
    with pytest.raises(ValueError):evaluate(c)
    c=config();c['options']=[{'name':'bad','cost':float('nan'),'residual_error':1.}]
    with pytest.raises(ValueError):evaluate(c)
    c=config();c['options']=[{'name':'same','cost':0.,'residual_error':1.},{'name':'same','cost':1.,'residual_error':0.}]
    with pytest.raises(ValueError):evaluate(c)
    c=config();c['options']=[{'name':'expensive','cost':2.,'residual_error':.1}]
    with pytest.raises(RuntimeError,match='allocation failed'):evaluate(c)


def test_acyclic_directed_graph_projection_is_not_a_circular_payment_claim():
    r=allocate_flow_review(3,[(0,1),(1,2),(0,2)],[[10.,10.,10.]],budget=1.)
    assert r['baseline_cycle_energy'][0]==pytest.approx(100./3.)
    assert 'does not establish a directed circular payment' in r['assumptions'][0]
