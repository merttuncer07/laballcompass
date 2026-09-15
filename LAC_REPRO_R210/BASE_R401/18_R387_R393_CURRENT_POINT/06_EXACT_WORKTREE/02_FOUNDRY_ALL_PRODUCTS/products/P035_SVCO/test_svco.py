from .svco import *
def R(): return svco({1.:1.5,2.:2.2,3.:2.4},steps=100,regeneration=.05,burnout=.02,min_active=.25)
def test_static_volcano_choice_visible(): assert R()['static_choice']==3
def test_state_changes_optimum(): assert R()['stateful_choice']==2
def test_same_cycle_for_all_candidates(): assert len(R()['rows'])==3

