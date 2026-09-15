from .cacf import *
E=[('A','B',10),('B','C',10),('C','A',10)]
def test_controlled_cycle_fraction_one(): assert cacf(E,{'A','B','C'})['controlled_fraction']==1
def test_partial_control_not_full(): assert cacf(E,{'A','B'})['controlled_fraction']<1
def test_zero_flow_safe(): assert cacf([],set())['controlled_fraction']==0

