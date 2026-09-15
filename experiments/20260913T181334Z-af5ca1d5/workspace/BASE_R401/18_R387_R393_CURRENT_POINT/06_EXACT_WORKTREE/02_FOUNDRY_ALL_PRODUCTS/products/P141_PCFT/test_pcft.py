import numpy as np
from .pcft import *
def seq():
    rng=np.random.default_rng(0); probs={(0,0):.6232655185893089,(0,1):.29280804238748326,(1,0):.08687617154257521,(1,1):.06487487197567618}; s=[0,1]
    for _ in range(400): s.append(int(rng.random()<probs[(s[-2],s[-1])]))
    return s
def R(): return predictive_closure_fidelity_tipping(seq(),history_length=2,tolerance_grid=[0,.02,.05,.1,.2,.5,1],baseline_tolerance=.05,allowed_closure_rate=.1,min_predictive_improvement=.05)
def test_baseline_safe(): assert R().surface['baseline_decision'] is True
def test_nearest_flip_at_point_one(): assert abs(R().surface['tipping_point']['parameters']['merge_tolerance']-.1)<1e-12
def test_degenerate_one_state_not_false_safe(): assert R().surface['metric_minimum']<0
def test_baseline_has_four_states(): assert R().baseline_state_count==4
def test_surface_contains_flip(): assert R().surface['status']=='TIPPING_POINT_FOUND'
def test_joint_margin_uses_fidelity(): assert R().surface['one_way_tipping_values']['merge_tolerance']==.1
