import numpy as np
from .bapc import *
U=np.array([[1,0],[0,2.]])
def test_persuasion_channel_has_decision_value(): assert bapc([[.9,.1],[.2,.8]],U,[.7,.3])['receiver_value']>0
def test_channel_more_informative_than_none(): assert bapc([[.9,.1],[.2,.8]],U,[.7,.3])['more_informative_than_none']
def test_not_mislabeled_full_revelation(): assert bapc([[.9,.1],[.2,.8]],U,[.7,.3])['less_informative_than_full_revelation']

