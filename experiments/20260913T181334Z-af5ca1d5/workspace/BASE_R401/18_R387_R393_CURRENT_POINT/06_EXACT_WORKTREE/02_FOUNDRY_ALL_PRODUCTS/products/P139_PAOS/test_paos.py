from .paos import *
SEL=[.1,.15,.2,.25,.3,.35]
HOLD=[-1.35,-1.4,-1.45,-1.5,-1.55,-1.6]
def R(): return audit_operator_averaging(SEL,HOLD,bootstrap_samples=400)
def test_selection_prefers_direct(): assert R().audit['selected_candidate']=='alpha_1'
def test_holdout_prefers_averaging(): assert R().audit['holdout_best_candidate']=='alpha_0.5'
def test_regret_material(): assert R().audit['selected_holdout_regret']>.1
def test_failure_detected(): assert R().audit['status']=='ADAPTIVE_SELECTION_REGRET_DETECTED'
def test_alpha_family_visible(): assert R().alpha_candidates==(1.0,.5)
def test_holdout_gap_large():
    r=R().audit; assert r['holdout_mean_losses'][0]>100*r['holdout_mean_losses'][1]
