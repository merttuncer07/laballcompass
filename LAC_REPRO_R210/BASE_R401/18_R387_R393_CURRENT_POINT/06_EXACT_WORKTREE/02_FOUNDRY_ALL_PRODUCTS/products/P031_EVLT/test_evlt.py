from .evlt import *
S=[(.8,set()),(.1,{'A'}),(.1,{'B'})]
def test_audit_subset_is_optimized(): assert evlt(S,{'A':100,'B':60},audit_slots=1,channel_capacity=80,anchor_cap=80)['selected']==('A',)
def test_capacity_makes_portfolio_nonadditive(): assert evlt(S,{'A':100,'B':60},audit_slots=2,channel_capacity=80,anchor_cap=80)['expected_liquidity']<=80
def test_culprit_scenario_blocks_verification(): assert evlt([(1,{'A'})],{'A':100},audit_slots=1,channel_capacity=100,anchor_cap=100)['expected_liquidity']==0

