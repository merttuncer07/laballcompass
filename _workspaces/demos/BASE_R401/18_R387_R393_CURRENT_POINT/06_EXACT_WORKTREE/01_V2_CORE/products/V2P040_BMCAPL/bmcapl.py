from __future__ import annotations
import numpy as np

def tipping_distance(records, baseline):
    if not records: raise ValueError('records required')
    if 'parameter' not in baseline or 'decision' not in baseline: raise ValueError('baseline needs parameter/decision')
    flips=[r for r in records if bool(r.get('decision')) != bool(baseline['decision'])]
    return None if not flips else min(abs(float(r['parameter'])-float(baseline['parameter'])) for r in flips)

def belief_margin_constrained_policy(learner, train_x, train_r, val_x, val_r, records, baseline, *, base_turnover, safe_margin, learner_kwargs):
    """BMDT tipping distance changes CAPL's feasible turnover set, not merely a report/gate."""
    if base_turnover<=0 or safe_margin<=0: raise ValueError('positive turnover/margin required')
    d=tipping_distance(records,baseline)
    factor=1.0 if d is None else min(1.0,max(0.0,d/float(safe_margin)))
    effective=max(1e-6,float(base_turnover)*factor)
    candidate=learner(train_x,train_r,val_x,val_r,maximum_turnover=effective,**learner_kwargs)
    control=learner(train_x,train_r,val_x,val_r,maximum_turnover=float(base_turnover),**learner_kwargs)
    return {
      'tipping_distance':d,'turnover_factor':factor,'effective_turnover':effective,'base_turnover':float(base_turnover),
      'candidate_validation_objective':float(candidate.validation_metrics.objective),
      'control_validation_objective':float(control.validation_metrics.objective),
      'gain_vs_removed_mechanism':float(control.validation_metrics.objective-candidate.validation_metrics.objective),
      'candidate_average_turnover':float(candidate.validation_metrics.average_turnover),
      'control_average_turnover':float(control.validation_metrics.average_turnover),
      'candidate_status':candidate.status,'control_status':control.status,
      'status':'BELIEF_MARGIN_CHANGED_POLICY_FEASIBLE_SET' if effective < base_turnover else 'BMDT_NO_TURNOVER_RESTRICTION'
    }
