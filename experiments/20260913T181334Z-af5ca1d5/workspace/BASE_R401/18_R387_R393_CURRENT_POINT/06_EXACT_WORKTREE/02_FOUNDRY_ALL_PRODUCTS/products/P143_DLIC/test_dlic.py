from .dlic import *
from .parents.lcm import Claim,FundingChannel
def base(advance=1.0,cap=10,max_anchor=1.0):
    c=[Claim('c1',5,'A','inv','v',True),Claim('c2',5,'B','inv','v',True)]
    ch=[FundingChannel('x',cap,('v',),('inv',),advance,max_anchor),FundingChannel('y',cap,('v',),('inv',),advance,max_anchor)]
    return c,ch
def test_unit_rate_integer_rhs_certified():
    c,ch=base(); r=audit_liquidity_integrality(c,ch); assert r.discrete_unit_interpretation_certified; assert r.tu_certificate['is_totally_unimodular']
def test_fractional_advance_drops_certificate():
    c,ch=base(.8); r=audit_liquidity_integrality(c,ch); assert not r.discrete_unit_interpretation_certified
def test_fractional_anchor_rhs_drops_certificate():
    c,ch=base(1.0,10,.35); r=audit_liquidity_integrality(c,ch); assert not r.integer_rhs; assert not r.discrete_unit_interpretation_certified
def test_lcm_still_solves_without_discrete_certificate():
    c,ch=base(.8); r=audit_liquidity_integrality(c,ch); assert r.lcm_result['deployable_liquidity']>0
def test_status_is_explicit():
    c,ch=base(.8); assert 'CONTINUOUS_ALLOCATION_ONLY' in audit_liquidity_integrality(c,ch).status
def test_matrix_small_and_exact():
    c,ch=base(); r=audit_liquidity_integrality(c,ch); assert len(r.constraint_matrix)<=10
