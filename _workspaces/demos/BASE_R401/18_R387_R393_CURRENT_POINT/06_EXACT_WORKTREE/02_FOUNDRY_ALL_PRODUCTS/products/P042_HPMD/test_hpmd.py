from .hpmd import *
E={'best':1031,'high':1129}; W={'best':.55,'high':.45}
def test_hidden_model_belief_can_change_action(): assert hpmd(E,W,[950,1050,1150],shortage_cost=2,excess_cost=1)['belief_action']==1150
def test_collapse_regret_nonnegative(): assert hpmd(E,W,[950,1050,1150],shortage_cost=2,excess_cost=1)['collapse_regret']>=0
def test_action_is_declared_capacity(): assert hpmd(E,W,[950,1050,1150],shortage_cost=2,excess_cost=1)['point_action'] in [950,1050,1150]
