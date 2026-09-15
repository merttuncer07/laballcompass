from .cars import *
from .parents.tsrc import FeatureSpec
from .parents.acra import ResolutionOption

def setup():
    feats=[FeatureSpec('critical',1.0,.20,1),FeatureSpec('secondary',.5,.10,1),FeatureSpec('nuisance',.02,1.0,10)]
    opts=[ResolutionOption('coarse',1,1,0),ResolutionOption('fine',3,.05,0)]
    return feats,opts

def test_deleted_feature_zero_weight():
    f,o=setup(); r=allocate_certificate_aware_resolution(f,protected_margin=.08,options=o,budget=5)
    assert 'nuisance' in r.certificate['deleted_features']; assert r.consequence_weights['nuisance']==0

def test_fine_goes_to_retained_critical():
    f,o=setup(); r=allocate_certificate_aware_resolution(f,protected_margin=.08,options=o,budget=5)
    m={x['region']:x['option'] for x in r.allocation['allocations']}; assert m['critical']=='fine'; assert m['nuisance']=='coarse'

def test_budget_respected():
    f,o=setup(); r=allocate_certificate_aware_resolution(f,protected_margin=.08,options=o,budget=5); assert r.allocation['total_cost']<=5+1e-9

def test_no_deleted_feature_can_win_on_noise_size():
    f,o=setup(); r=allocate_certificate_aware_resolution(f,protected_margin=.08,options=o,budget=5); assert r.consequence_weights['critical']>r.consequence_weights['nuisance']

def test_status():
    f,o=setup(); assert allocate_certificate_aware_resolution(f,protected_margin=.08,options=o,budget=5).status.startswith('CERTIFICATE')

def test_tight_margin_retains_more():
    f,o=setup(); r=allocate_certificate_aware_resolution(f,protected_margin=.015,options=o,budget=5); assert 'nuisance' not in r.certificate['deleted_features']
