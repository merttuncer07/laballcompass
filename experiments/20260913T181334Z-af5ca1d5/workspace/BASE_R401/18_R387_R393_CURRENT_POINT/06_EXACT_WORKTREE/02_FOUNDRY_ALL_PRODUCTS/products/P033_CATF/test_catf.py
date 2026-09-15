from .catf import *
R=[{'time_weight':10,'frequency_weight':1},{'time_weight':1,'frequency_weight':10}]
O=[{'name':'short','time_spread':1,'frequency_spread':4,'cost':2},{'name':'long','time_spread':4,'frequency_spread':1,'cost':2}]
def test_regions_receive_different_windows(): assert catf(R,O,budget=4)['allocation']==('short','long')
def test_shared_budget_respected(): assert catf(R,O,budget=4)['cost']<=4
def test_adaptive_beats_fixed(): assert catf(R,O,budget=4)['improvement_fraction']>0

