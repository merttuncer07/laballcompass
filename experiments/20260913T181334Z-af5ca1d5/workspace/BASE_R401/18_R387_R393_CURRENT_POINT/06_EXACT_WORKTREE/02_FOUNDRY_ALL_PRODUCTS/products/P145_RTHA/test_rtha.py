import numpy as np
from .rtha import *
def batches():
    rng=np.random.default_rng(0); s=[]; h=[]
    for _ in range(30):
        s.append(np.where(rng.random(40)<.8,rng.uniform(1.5,2.5,40),rng.uniform(30,50,40)))
        # Holdout remains light-tailed but retains a few sub-threshold jobs, so threshold=3 is
        # finite rather than being rejected only because no job can finish before restart.
        h.append(np.where(rng.random(40)<.1,rng.uniform(2.5,2.9,40),rng.uniform(3.5,4.5,40)))
    return s,h
TH=[3.0,None,5.0,10.0]
def R():
    s,h=batches(); return audit_restart_thresholds(s,h,thresholds=TH,restart_overhead=.2,bootstrap_samples=400)
def test_selection_prefers_restart(): assert R().audit['selected_candidate']=='threshold_3'
def test_holdout_prefers_no_restart(): assert R().audit['holdout_best_candidate']=='no_restart'
def test_regret_material(): assert R().audit['selected_holdout_regret']>20
def test_status_detects(): assert R().audit['status']=='ADAPTIVE_SELECTION_REGRET_DETECTED'
def test_candidate_family_visible(): assert R().candidate_names==('threshold_3','no_restart','threshold_5','threshold_10')
def test_holdout_restart_three_is_finite_but_bad():
    r=R().audit; assert r['holdout_mean_losses'][0]<100 and r['holdout_mean_losses'][0]>5*r['holdout_mean_losses'][1]
