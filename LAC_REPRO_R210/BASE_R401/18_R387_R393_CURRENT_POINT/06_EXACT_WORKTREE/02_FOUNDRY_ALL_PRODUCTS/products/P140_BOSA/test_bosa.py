from .bosa import *
def R(): return audit_burnout_support(cohort_size=10000,base_rates=[.03]*24,propensity_multipliers=[.2,1,5],initial_class_weights=[.3,.4,.3],months_to_audit=[1,6,12,24],fragile_ess_fraction=.8)
def test_early_support_usable(): assert R().points[0].support_status=='SUPPORT_USABLE'
def test_late_support_fragile(): assert R().points[-1].support_status=='SUPPORT_FRAGILE'
def test_first_fragile_month(): assert R().first_fragile_month==12
def test_ess_erodes():
    r=R(); assert r.points[0].effective_sample_fraction>.99 and r.points[-1].effective_sample_fraction<.7
def test_high_propensity_class_burns_out(): assert R().points[-1].class_survival_ratios[-1]<.03
def test_naive_model_overpredicts(): assert R().naive_overprediction_fraction>0
