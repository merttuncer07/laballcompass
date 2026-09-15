import numpy as np
from .ogrm import *
def test_risky_mode_can_be_unobservable(): assert 'UNOBSERVABLE' in ogrm(np.diag([.95,.4]),np.array([[0,1]]),np.array([1,0]),exposure=1,recovery_steps=59)['status']
def test_measurement_change_makes_visible(): assert ogrm(np.diag([.95,.4]),np.array([[1,1]]),np.array([1,0]),exposure=1,recovery_steps=59)['observable']
def test_gain_reported(): assert ogrm(np.eye(2),np.array([[1,0]]),np.array([1,0]),exposure=1,recovery_steps=1)['measurement_gain']==1

