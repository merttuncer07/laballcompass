import numpy as np
from .qaig import *
from .parents.aicc import InformationChannel

X=np.linspace(-2,2,101); base=np.exp(-X**2)
KW=dict(electron_mobility=2,hole_mobility=1,electron_diffusivity=1,hole_diffusivity=.5)
CH=[InformationChannel('precise',np.array([1.]),.0001,.002),InformationChannel('coarse',np.array([1.]),.01,.01)]
def prof(delta): return base*(1+delta/2),base*(1-delta/2)
def test_near_boundary_measures():
    n,p=prof(.049); r=gate_quasineutral_measurement(X,n,p,transport_kwargs=KW,belief_variance=.0004,channels=CH); assert r.chosen_channel=='precise'
def test_far_boundary_skips():
    n,p=prof(.005); r=gate_quasineutral_measurement(X,n,p,transport_kwargs=KW,belief_variance=.000025,channels=CH); assert r.chosen_channel is None
def test_imbalance_tracks_profile():
    n,p=prof(.049); r=gate_quasineutral_measurement(X,n,p,transport_kwargs=KW,belief_variance=.0004,channels=CH); assert .045<r.imbalance<.055
def test_ranked_channel_has_net_value():
    n,p=prof(.049); r=gate_quasineutral_measurement(X,n,p,transport_kwargs=KW,belief_variance=.0004,channels=CH); assert r.ranked_channels[0]['net_value']>0
def test_transport_status_preserved():
    n,p=prof(.08); r=gate_quasineutral_measurement(X,n,p,transport_kwargs=KW,belief_variance=.0004,channels=CH); assert r.transport_status=='QUASINEUTRAL_PACKET_ASSUMPTION_EXCEEDED'
def test_status_contract():
    n,p=prof(.005); assert 'VALIDITY_BOUNDARY' in gate_quasineutral_measurement(X,n,p,transport_kwargs=KW,belief_variance=.000025,channels=CH).status
