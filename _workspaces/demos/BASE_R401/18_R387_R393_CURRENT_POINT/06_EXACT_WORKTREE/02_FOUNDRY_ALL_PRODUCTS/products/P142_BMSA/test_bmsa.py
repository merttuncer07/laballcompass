from .bmsa import *
def R(): return audit_burnout_model_selection(bootstrap_samples=400)
def test_early_selection_prefers_homogeneous(): assert R().audit['selected_candidate']=='homogeneous'
def test_late_holdout_prefers_burnout(): assert R().audit['holdout_best_candidate']=='burnout_aware'
def test_material_regret_detected(): assert R().audit['selected_holdout_regret']>8000
def test_holdout_ratio_large():
    x=R().audit['holdout_mean_losses']; assert x[0]>100*x[1]
def test_status_detects_overfit(): assert R().audit['status']=='ADAPTIVE_SELECTION_REGRET_DETECTED'
def test_truth_has_positive_prepayment(): assert R().truth_cumulative_prepayments>0
