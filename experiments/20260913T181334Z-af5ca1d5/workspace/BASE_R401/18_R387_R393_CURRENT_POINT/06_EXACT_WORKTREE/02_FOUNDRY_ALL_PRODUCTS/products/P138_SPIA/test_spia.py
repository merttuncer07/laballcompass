import numpy as np
from .spia import *
from .parents.aicc import InformationChannel
P=[('local',8,0),('intermittent',2,3)]
v=np.zeros(8); v[5]=1; v[3]=-1
C=.0025*np.outer(v,v)
CH=[InformationChannel('hotspot_contrast',v,.001,.02)]
def near(): return np.array([.12,0,0,.40,0,.48,0,0])
def far(): return np.array([.12,0,0,.70,0,.18,0,0])
def test_near_boundary_acquires():
    r=acquire_for_search_policy(near(),C,policies=P,channels=CH); assert r.chosen_channel=='hotspot_contrast'; assert r.ranked_channels[0]['net_value']>.08
def test_far_boundary_skips():
    r=acquire_for_search_policy(far(),C,policies=P,channels=CH); assert r.chosen_channel is None; assert r.ranked_channels[0]['net_value']<0
def test_expected_time_is_linear_policy_utility():
    r=acquire_for_search_policy(near(),C,policies=P,channels=CH); t=np.array(r.detection_time_vectors); e=t@near(); assert abs(e[0]-e[1])<1e-12
def test_covariance_must_preserve_probability_sum():
    bad=np.eye(8)*.01
    try: acquire_for_search_policy(near(),bad,policies=P,channels=CH)
    except ValueError: return
    assert False
def test_channel_must_be_contrast():
    bad=[InformationChannel('bad',np.ones(8),.1,0)]
    try: acquire_for_search_policy(near(),C,policies=P,channels=bad)
    except ValueError: return
    assert False
def test_policy_vectors_cover_all_locations():
    r=acquire_for_search_policy(near(),C,policies=P,channels=CH); assert np.all(np.isfinite(r.detection_time_vectors))
