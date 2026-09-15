from .sara import *
def test_structural_order_labeled_structural(): assert sara(structural_dimension=2,selected_order=2,error_bound=.1)['status']=='STRUCTURAL_REDUNDANCY_ONLY'
def test_below_structural_dimension_is_approximate(): assert 'APPROXIMATE' in sara(structural_dimension=2,selected_order=1,error_bound=.48)['status']
def test_error_bound_preserved(): assert sara(structural_dimension=2,selected_order=1,error_bound=.48)['error_bound']==.48

