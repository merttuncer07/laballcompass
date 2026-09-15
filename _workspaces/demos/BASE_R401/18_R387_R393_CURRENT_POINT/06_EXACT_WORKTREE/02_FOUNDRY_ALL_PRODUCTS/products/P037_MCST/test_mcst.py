from .mcst import *
def V(x): return max(0,-2-x)
def test_nearest_break_found(): assert mcst([-2.1,-2,-1.8],V,baseline=-1.8)['tipping_value']==-2.1
def test_weak_zero_still_passes(): assert mcst([-2],V,baseline=-2)['baseline_violation']==0
def test_no_grid_failure_explicit(): assert mcst([-2,-1.8],V,baseline=-1.8)['tipping_value'] is None

