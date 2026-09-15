from .bdts import *
P=[{'parameter':2,'bottleneck':2,'jump':1.33},{'parameter':3,'bottleneck':3,'jump':1.67}]
def test_joint_threshold_flip(): assert bdts(P,bottleneck_threshold=3,jump_threshold=1.6,baseline=2)['tipping_parameter']==3
def test_both_conditions_required(): assert not bdts([{'parameter':3,'bottleneck':3,'jump':1.2}],bottleneck_threshold=3,jump_threshold=1.6,baseline=2)['breakthrough']
def test_margin_nonnegative_at_flip(): assert bdts(P,bottleneck_threshold=3,jump_threshold=1.6,baseline=2)['margin']>=0

