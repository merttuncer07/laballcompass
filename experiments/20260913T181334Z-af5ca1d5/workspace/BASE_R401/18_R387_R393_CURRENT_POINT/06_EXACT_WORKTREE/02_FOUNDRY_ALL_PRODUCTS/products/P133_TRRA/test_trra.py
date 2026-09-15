from .trra import *

def test_identity_preserved(): assert PRODUCT_SPEC['product_id'].startswith('P') and PRODUCT_SPEC['short_name']
def test_reconstruction_tier_explicit():
 records=[{'name':'a','score':1,'value':1,'cost':1,'parameter':0,'decision':False,'selection_score':2,'protected_score':0},{'name':'b','score':2,'value':2,'cost':1,'parameter':1,'decision':True,'selection_score':1,'protected_score':3}]
 kwargs={'budget':1} if PRODUCT_SPEC['execution_mode']=='allocation' else ({'baseline':records[0]} if PRODUCT_SPEC['execution_mode']=='tipping' else {})
 assert evaluate(records,**kwargs)['reconstruction_tier']=='SPEC_EXECUTABLE_NOT_HISTORICAL_SOURCE'
def test_empty_input_rejected():
 try: evaluate([])
 except ValueError: return
 assert False
