import numpy as np
from .dpai import *
from .parents.dfdpe import simulate_affine_dynamics
from .parents.aicc import InformationChannel
CH=[InformationChannel('identification_experiment',np.array([1.]),.0025,.005)]
def case(a,noise,seed,ntrain):
    rng=np.random.default_rng(seed); t=np.linspace(0,10,101); u=np.sin(t)+.5*np.cos(1.7*t); y=simulate_affine_dynamics(t,u,1,[a,.6,.05]); obs=y+rng.normal(0,noise,len(t))
    return identify_persistence_then_acquire(t[:ntrain],obs[:ntrain],u[:ntrain],window_duration=2,window_step=.5,channels=CH)
def test_uncertain_boundary_case_measures():
    r=case(-.03,.25,2,70); assert r.chosen_channel=='identification_experiment'; assert r.ranked_channels[0]['net_value']>.03
def test_far_stable_case_skips():
    r=case(-.5,.05,4,90); assert r.chosen_channel is None; assert r.ranked_channels[0]['net_value']<0
def test_near_case_uncertainty_material(): assert case(-.03,.25,2,70).persistence_standard_error>.08
def test_far_case_precise(): assert case(-.5,.05,4,90).persistence_standard_error<.02
def test_action_label_exposed(): assert case(-.5,.05,4,90).current_action=='STABLE_SIDE'
def test_status_contract(): assert 'PERSISTENCE' in case(-.03,.25,2,70).status
