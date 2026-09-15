from .sgot import *
def test_good_overlap_passes(): assert sgot(2,.1,[.5]*10,[0,1]*5)['deploy']
def test_concentrated_weights_block(): assert not sgot(5,.03,[.99]*99+[.01],[1]*99+[0])['deploy']
def test_uniform_extreme_propensity_floor_blocks(): assert not sgot(2,.1,[.99]*10,[1]*10)['deploy']

