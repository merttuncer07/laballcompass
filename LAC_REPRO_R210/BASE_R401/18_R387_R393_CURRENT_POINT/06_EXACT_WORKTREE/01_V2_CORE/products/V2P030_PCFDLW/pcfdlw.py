from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import sys
_REPO=Path(__file__).resolve().parents[3]
_D=_REPO/'02_FOUNDRY_ALL_PRODUCTS'/'parent_products'/'RETRO_PRODUCTS'/'R044_DECISION_LOSS_DLEW'
if str(_D) not in sys.path: sys.path.insert(0,str(_D))
from dlew import evaluate_decision_models

@dataclass(frozen=True)
class Result:
    certified_candidates:tuple[str,...]
    rejected_candidates:tuple[str,...]
    selected:str|None
    blind_selected:str
    decision_result:dict|None
    blind_validation_regret:float
    guarded_validation_regret:float|None
    status:str
    def to_dict(self): return asdict(self)

def closure_fidelity_decision_selection(training_predictions,training_outcomes,validation_predictions,validation_outcomes,action_payoff_exposures,*,initial_action_exposure,closure_violation,predictive_improvement,allowed_closure_rate,min_predictive_improvement,transaction_cost=0.):
    names=sorted(training_predictions)
    if set(names)!=set(validation_predictions) or set(names)!=set(closure_violation) or set(names)!=set(predictive_improvement): raise ValueError('candidate keys must match')
    blind=evaluate_decision_models(training_predictions,training_outcomes,validation_predictions,validation_outcomes,action_payoff_exposures,initial_action_exposure=initial_action_exposure,transaction_cost=transaction_cost)
    ok=[n for n in names if closure_violation[n]<=allowed_closure_rate and predictive_improvement[n]>=min_predictive_improvement]
    bad=[n for n in names if n not in ok]
    if not ok: return Result(tuple(),tuple(bad),None,blind.selected_by_training_decision_loss,None,float(blind.selected_validation_decision_regret),None,'NO_CLOSURE_FIDELITY_CERTIFIED_CANDIDATE')
    tp={n:training_predictions[n] for n in ok}; vp={n:validation_predictions[n] for n in ok}
    guarded=evaluate_decision_models(tp,training_outcomes,vp,validation_outcomes,action_payoff_exposures,initial_action_exposure=initial_action_exposure,transaction_cost=transaction_cost)
    return Result(tuple(ok),tuple(bad),guarded.selected_by_training_decision_loss,blind.selected_by_training_decision_loss,guarded.to_dict(),float(blind.selected_validation_decision_regret),float(guarded.selected_validation_decision_regret),'CLOSURE_FIDELITY_GATED_DECISION_SELECTION')
