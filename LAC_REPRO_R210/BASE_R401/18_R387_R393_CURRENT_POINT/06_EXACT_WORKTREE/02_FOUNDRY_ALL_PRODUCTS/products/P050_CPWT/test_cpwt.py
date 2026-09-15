from .cpwt import *
P=[{'parameter':.1,'radius':1.1,'volume_error':.001},{'parameter':.4,'radius':1.31,'volume_error':.004},{'parameter':.8,'radius':1.4,'volume_error':.012}]
def test_valid_target_selected(): assert cpwt(P,target_radius=1.3,max_volume_error=.005,baseline=.1)['selected_parameter']==.4
def test_nominal_target_with_bad_conservation_rejected(): assert .8 in cpwt(P,target_radius=1.3,max_volume_error=.005,baseline=.1)['conservation_rejected_parameters']
def test_no_valid_point_explicit(): assert not cpwt(P,target_radius=2,max_volume_error=.005,baseline=.1)['valid_target_found']

