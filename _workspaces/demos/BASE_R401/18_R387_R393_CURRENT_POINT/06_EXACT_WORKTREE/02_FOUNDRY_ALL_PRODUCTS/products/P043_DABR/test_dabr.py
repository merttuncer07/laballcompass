from .dabr import *
C=[{'order':1,'error_bound':.48,'protected_regret':.023},{'order':2,'error_bound':.034,'protected_regret':.0001}]
def test_generic_prefers_smallest_order(): assert dabr(C,generic_error_budget=.5)['generic_order']==1
def test_decision_audit_prefers_order_two(): assert dabr(C,generic_error_budget=.5)['decision_order']==2
def test_protected_regret_reduced(): assert dabr(C,generic_error_budget=.5)['decision_regret']<dabr(C,generic_error_budget=.5)['generic_regret']

