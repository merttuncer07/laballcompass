
from __future__ import annotations
import numpy as np
from scipy.stats import norm

def tipping_reset_calibration(mcst_fn, controller_cls, summarize_fn, *, stress_series,
        target_coverage=.90, initial_multiplier=1.645, seed=2, reset_enabled=True):
    """Use an MCST calibration-violation surface to reset CWC at a mechanism/stress break.

    The declared stress variable is externally observed.  CWC itself receives a frozen
    base_scale=1, so without the supplier it must learn the width change only from misses.
    Removal control uses the same outcomes and same CWC but ignores the tipping signal.
    """
    stress=np.asarray(stress_series,float)
    if stress.ndim!=1 or len(stress)<40 or np.any(stress<=0): raise ValueError('positive stress series required')
    alpha=1-float(target_coverage)
    grid=sorted(set(float(x) for x in np.linspace(max(.5,stress.min()),stress.max(),31)))
    def violation(s): return float(2*(1-norm.cdf(float(initial_multiplier)/float(s)))-alpha)
    tip=mcst_fn(grid,violation,baseline=float(stress[0]),tolerance=0.)
    c=controller_cls(target_coverage=target_coverage,proportional_gain=.08,integral_gain=.002,initial_multiplier=initial_multiplier)
    rng=np.random.default_rng(seed); obs=[]; resets=0; prev=float(stress[0])
    for s in stress:
        s=float(s)
        crossed=tip['tipping_value'] is not None and s>=float(tip['tipping_value']) and prev<float(tip['tipping_value'])
        if reset_enabled and crossed:
            # Calibration surface says the nominal multiplier has crossed its miss-rate boundary.
            c.log_multiplier=float(np.log(initial_multiplier*s)); c.coverage_ewma=c.target; c.integral=0.; resets+=1
        y=float(rng.normal(0,s)); obs.append(c.observe(y,0.,1.)); prev=s
    summary=summarize_fn(obs,target_coverage,window=20)
    post_start=next((i for i in range(1,len(stress)) if stress[i]!=stress[i-1]),len(stress))
    post=obs[post_start:min(len(obs),post_start+20)]
    summary.update({'tipping_value':tip['tipping_value'],'tipping_status':tip['status'],'resets':resets,
                    'post_shift_coverage_20':float(np.mean([o.covered for o in post])) if post else None,
                    'post_shift_interval_score_20':float(np.mean([o.interval_score for o in post])) if post else None})
    return summary

def compare(mcst_fn,controller_cls,summarize_fn,stress_series,**kwargs):
    a=tipping_reset_calibration(mcst_fn,controller_cls,summarize_fn,stress_series=stress_series,reset_enabled=True,**kwargs)
    b=tipping_reset_calibration(mcst_fn,controller_cls,summarize_fn,stress_series=stress_series,reset_enabled=False,**kwargs)
    return {'candidate':a,'mechanism_removed':b,
            'interval_score_gain':b['mean_interval_score']-a['mean_interval_score'],
            'rolling_coverage_rmse_gain':b['rolling_coverage_rmse']-a['rolling_coverage_rmse'],
            'post_shift_coverage_gain':None if a['post_shift_coverage_20'] is None or b['post_shift_coverage_20'] is None else a['post_shift_coverage_20']-b['post_shift_coverage_20'],
            'status':'TIPPING_RESET_IMPROVES_SHIFT_CALIBRATION' if a['mean_interval_score']<b['mean_interval_score'] else 'NO_RESET_GAIN'}
