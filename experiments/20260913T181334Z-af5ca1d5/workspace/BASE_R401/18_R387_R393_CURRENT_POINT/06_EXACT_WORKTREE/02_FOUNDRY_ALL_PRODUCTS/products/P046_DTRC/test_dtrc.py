from .dtrc import *
C=[{'name':'mean','report':50,'strictly_truthful':True},{'name':'q80','report':80,'strictly_truthful':True},{'name':'clipped','report':90,'strictly_truthful':False}]
Y=[20,40,60,80,100]
def test_decision_target_can_differ_from_rmse(): assert dtrc(C,Y,shortage_cost=4,excess_cost=1)['decision_contract']=='q80'
def test_prediction_prefers_mean(): assert dtrc(C,Y,shortage_cost=4,excess_cost=1)['prediction_contract']=='mean'
def test_invalid_contract_excluded(): assert dtrc(C,Y,shortage_cost=4,excess_cost=1)['decision_contract']!='clipped'

