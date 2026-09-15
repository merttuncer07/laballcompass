from .vcts import *

R=[{'name':'a','score':1,'value':1,'cost':1,'parameter':0,'decision':False,'selection_score':2,'protected_score':0},{'name':'b','score':2,'value':2,'cost':1,'parameter':1,'decision':True,'selection_score':1,'protected_score':3}]
def kwargs(): return {'budget':1} if PRODUCT_SPEC['execution_mode']=='allocation' else ({'baseline':R[0]} if PRODUCT_SPEC['execution_mode']=='tipping' else {})
def test_gap_identity_explicit(): assert PRODUCT_SPEC['product_id']=='P052'
def test_new_replacement_tier_explicit(): assert evaluate(R,**kwargs())['reconstruction_tier']=='NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID'
def test_parent_composition_declared(): assert '+' in PRODUCT_SPEC['parents_raw']
def test_execution_returns_status(): assert evaluate(R,**kwargs())['status']
