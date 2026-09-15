from __future__ import annotations
import numpy as np

def dominance_tipping(records,baseline):
    flips=[r for r in records if bool(r.get('decision')) != bool(baseline.get('decision'))]
    return None if not flips else min(flips,key=lambda r:abs(float(r['parameter'])-float(baseline['parameter'])))

def channel_tipping_robust_selection(evaluator, train_outcomes, val_outcomes, regime_predictions, action_exposures, *, baseline_channel, dominance_records, initial_action_exposure, transaction_cost=0.0, evaluation_channel=None):
    """CDTS defines the channel-regime set; DLEW regret defines the minimax model-selection objective."""
    tip=dominance_tipping(dominance_records,baseline_channel)
    upper=float(baseline_channel['parameter']) if tip is None else float(tip['parameter'])
    lo=min(float(baseline_channel['parameter']),upper); hi=max(float(baseline_channel['parameter']),upper)
    protected=[q for q in sorted(regime_predictions) if lo-1e-12 <= float(q) <= hi+1e-12]
    if not protected: raise ValueError('no declared predictions in protected channel interval')
    per={}; names=None
    for q in protected:
      trp,vap=regime_predictions[q]
      res=evaluator(trp,train_outcomes,vap,val_outcomes,action_exposures,initial_action_exposure=initial_action_exposure,transaction_cost=transaction_cost)
      rows={c.name:float(c.mean_decision_regret) for c in res.training_candidates}; per[str(q)]=rows; names=set(rows) if names is None else names & set(rows)
    worst={n:max(per[str(q)][n] for q in protected) for n in names}
    candidate=min(worst,key=lambda n:(worst[n],n))
    q0=min(protected,key=lambda q:abs(float(q)-float(baseline_channel['parameter'])))
    tr0,va0=regime_predictions[q0]; base_res=evaluator(tr0,train_outcomes,va0,val_outcomes,action_exposures,initial_action_exposure=initial_action_exposure,transaction_cost=transaction_cost)
    baseline=base_res.selected_by_training_decision_loss
    qe=evaluation_channel if evaluation_channel is not None else protected[-1]
    tr_e,va_e=regime_predictions[qe]; eval_res=evaluator(tr_e,train_outcomes,va_e,val_outcomes,action_exposures,initial_action_exposure=initial_action_exposure,transaction_cost=transaction_cost)
    val={c.name:float(c.mean_decision_regret) for c in eval_res.validation_candidates}
    return {'tipping_parameter':None if tip is None else float(tip['parameter']),'protected_regimes':protected,'baseline_selected':baseline,'selected':candidate,'worst_case_training_regret':worst,'evaluation_channel':qe,'candidate_validation_regret':val[candidate],'baseline_validation_regret':val[baseline],'gain_vs_removed_mechanism':val[baseline]-val[candidate],'status':'CHANNEL_TIPPING_CHANGED_DLEW_SELECTION' if candidate!=baseline else 'CHANNEL_TIPPING_NO_SELECTION_CHANGE'}
