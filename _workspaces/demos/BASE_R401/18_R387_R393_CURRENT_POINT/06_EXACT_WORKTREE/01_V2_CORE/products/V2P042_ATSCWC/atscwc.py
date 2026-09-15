
from __future__ import annotations
import numpy as np

def _posterior_summary(sensor):
    idx=np.arange(sensor.n,dtype=float)
    mean=float(idx@sensor.posterior)
    var=float(((idx-mean)**2)@sensor.posterior)
    return mean,max(var**0.5,1e-9)

def compare_active_vs_fixed(sensor_cls, controller_cls, summarize_fn, *, n_locations=31,
                            response_accuracy=.82, query_budget=6, tasks=500, seed=0,
                            target_coverage=.90, controller_kwargs=None):
    """Couple active threshold selection to an online calibration controller.

    The supplier is not used as a post-hoc report: its adaptive query policy changes
    the center/scale stream seen by the CWC consumer.  The removal control uses the
    same sensor likelihood, same query budget, same random response draws, and same
    calibration controller, but replaces adaptive threshold selection with a frozen
    evenly-spaced query schedule.
    """
    if n_locations < 3 or query_budget < 1 or query_budget >= n_locations:
        raise ValueError('invalid location count or query budget')
    if not .5 < response_accuracy < 1:
        raise ValueError('response_accuracy must be in (.5,1)')
    kw=dict(proportional_gain=.08, integral_gain=.002, initial_multiplier=1.645)
    if controller_kwargs: kw.update(controller_kwargs)
    active_controller=controller_cls(target_coverage=target_coverage,**kw)
    fixed_controller=controller_cls(target_coverage=target_coverage,**kw)
    active_obs=[]; fixed_obs=[]
    master=np.random.default_rng(seed)
    truths=master.integers(0,n_locations,size=int(tasks))
    fixed_grid=np.linspace(0,n_locations-2,query_budget).round().astype(int)
    for task_index,true_index in enumerate(truths):
        # identical uniforms per query count; only the selected threshold differs
        u=np.random.default_rng(seed*1000003+task_index).random(query_budget)
        active=sensor_cls(n_locations,response_accuracy=response_accuracy)
        fixed=sensor_cls(n_locations,response_accuracy=response_accuracy)
        for j in range(query_budget):
            ta=active.choose()
            truth_a=bool(true_index <= ta)
            active.observe(ta, truth_a if u[j] < response_accuracy else not truth_a)
            tf=int(fixed_grid[j])
            truth_f=bool(true_index <= tf)
            fixed.observe(tf, truth_f if u[j] < response_accuracy else not truth_f)
        ma,sa=_posterior_summary(active); mf,sf=_posterior_summary(fixed)
        active_obs.append(active_controller.observe(float(true_index),ma,sa))
        fixed_obs.append(fixed_controller.observe(float(true_index),mf,sf))
    a=summarize_fn(active_obs,target_coverage,window=50)
    f=summarize_fn(fixed_obs,target_coverage,window=50)
    return {
      'active':a,'mechanism_removed_fixed_queries':f,
      'interval_score_gain':float(f['mean_interval_score']-a['mean_interval_score']),
      'mean_width_reduction':float(f['mean_width']-a['mean_width']),
      'rolling_coverage_rmse_gain':float(f['rolling_coverage_rmse']-a['rolling_coverage_rmse']),
      'status':'ACTIVE_SENSING_IMPROVES_CALIBRATED_INTERVAL_STREAM' if a['mean_interval_score'] < f['mean_interval_score'] else 'NO_ACTIVE_SENSING_GAIN'
    }
