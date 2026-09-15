"""Certificate-Aware Reduction Foundry (CARF) v0.1.

Route reductions by the property that must survive compression, and prevent a
certificate for one target from being silently promoted to another target.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Sequence
import numpy as np

if __package__:
    from .parents.corma import audit_state_space, StateSpaceAudit
else:
    from parents.corma import audit_state_space, StateSpaceAudit
if __package__:
    from .parents.bred import design_balanced_reduction, BalancedReduction
else:
    from parents.bred import design_balanced_reduction, BalancedReduction
if __package__:
    from .parents.twmr import TargetWeightedModelReducer, ReductionResult as TargetReduction
else:
    from parents.twmr import TargetWeightedModelReducer, ReductionResult as TargetReduction
if __package__:
    from .parents.tsrc import FeatureSpec, TargetSufficientReductionCertifier, ReductionCertificate
else:
    from parents.tsrc import FeatureSpec, TargetSufficientReductionCertifier, ReductionCertificate
if __package__:
    from .parents.ote import OrthogonalTargetEstimator, OrthogonalEstimate
else:
    from parents.ote import OrthogonalTargetEstimator, OrthogonalEstimate
if __package__:
    from .parents.salc import audit_lumpability, LumpabilityCertificate
else:
    from parents.salc import audit_lumpability, LumpabilityCertificate
if __package__:
    from .parents.dsbc import compress_beliefs, BeliefCompressionResult
else:
    from parents.dsbc import compress_beliefs, BeliefCompressionResult
if __package__:
    from .parents.psct import discover_predictive_states, PredictiveStateResult
else:
    from parents.psct import discover_predictive_states, PredictiveStateResult

class Requirement(str, Enum):
    FULL_IO_BEHAVIOR = "full_io_behavior"
    TARGET_OUTPUT_TRAJECTORY = "target_output_trajectory"
    THRESHOLD_ACTION = "threshold_action"
    CAUSAL_TARGET = "causal_target"
    MARKOV_CLOSED_DYNAMICS = "markov_closed_dynamics"
    DECISION_REGRET = "decision_regret"
    OBSERVABLE_PREDICTIVE_DYNAMICS = "observable_predictive_dynamics"

@dataclass(frozen=True)
class RouteRecommendation:
    requirement: Requirement
    products: tuple[str, ...]
    certificate_kind: str
    guarantee: str
    forbidden_promotion: str
    def to_dict(self): return asdict(self)

ROUTES = {
    Requirement.FULL_IO_BEHAVIOR: RouteRecommendation(Requirement.FULL_IO_BEHAVIOR,("CORMA","BRED"),"balanced_io_error_bound","global input-output approximation","does not by itself certify a causal target or decision regret"),
    Requirement.TARGET_OUTPUT_TRAJECTORY: RouteRecommendation(Requirement.TARGET_OUTPUT_TRAJECTORY,("CORMA","TWMR"),"target_impulse_error","specified future output trajectory","does not certify unprotected outputs"),
    Requirement.THRESHOLD_ACTION: RouteRecommendation(Requirement.THRESHOLD_ACTION,("TSRC",),"action_margin_certificate","threshold action invariance inside the declared shell","does not certify causal sufficiency"),
    Requirement.CAUSAL_TARGET: RouteRecommendation(Requirement.CAUSAL_TARGET,("OTE",),"orthogonal_target_estimate","orthogonalized target estimation conditional on supplied representation","does not prove the representation contains all confounders"),
    Requirement.MARKOV_CLOSED_DYNAMICS: RouteRecommendation(Requirement.MARKOV_CLOSED_DYNAMICS,("SALC",),"lumpability_certificate","closed aggregate Markov dynamics","does not certify decision sufficiency"),
    Requirement.DECISION_REGRET: RouteRecommendation(Requirement.DECISION_REGRET,("DSBC",),"decision_regret_certificate","bounded downstream decision regret","does not certify predictive/update closure"),
    Requirement.OBSERVABLE_PREDICTIVE_DYNAMICS: RouteRecommendation(Requirement.OBSERVABLE_PREDICTIVE_DYNAMICS,("PSCT",),"predictive_closure_certificate","observable predictive equivalence plus tested update closure","does not certify utility-specific decision optimality"),
}

def route_requirement(requirement: Requirement | str) -> RouteRecommendation:
    req = Requirement(requirement)
    return ROUTES[req]

@dataclass(frozen=True)
class LinearReductionComparison:
    audit: StateSpaceAudit
    balanced: BalancedReduction
    target_weighted: TargetReduction
    status: str


def compare_linear_reductions(a,b,c_all,c_target,*,error_budget:float,retain_count:int,horizon:int=30):
    audit=audit_state_space(a,b,c_all,horizon=max(len(a),horizon))
    if not audit.stable:
        raise ValueError("BRED route requires a stable system")
    balanced=design_balanced_reduction(a,b,c_all,error_budget=error_budget,minimum_order=1,impulse_horizon=horizon)
    target=TargetWeightedModelReducer(a,b,c_target).reduce(retain_count,horizon=horizon)
    return LinearReductionComparison(audit,balanced,target,"GLOBAL_AND_TARGET_REDUCTIONS_COMPARED_WITH_DISTINCT_CERTIFICATES")

@dataclass(frozen=True)
class ActionToCausalMismatchAudit:
    action_certificate: ReductionCertificate
    full_causal_estimate: OrthogonalEstimate
    reduced_causal_estimate: OrthogonalEstimate
    causal_target_drift: float
    causal_drift_in_full_standard_errors: float
    certificate_adequate_for_action: bool
    certificate_adequate_for_causal_target: bool
    status: str
    def to_dict(self): return asdict(self)


def audit_action_reduction_for_causal_target(
    values: Sequence[Sequence[float]], treatment: Sequence[float], outcome: Sequence[float],
    features: Sequence[FeatureSpec], *, thresholds=(0.0,), baselines=None, reserve:float=0.0,
    folds:int=5, seed:int=20260825,
) -> ActionToCausalMismatchAudit:
    x=np.asarray(values,dtype=float)
    certifier=TargetSufficientReductionCertifier(features,thresholds)
    margin=certifier.margin_on_values(x)
    cert=certifier.evaluate(certifier.optimize(margin,reserve=reserve),x,baselines=baselines)
    retained_names=set(cert.retained_features)
    indices=[i for i,f in enumerate(features) if f.name in retained_names]
    if not indices:
        raise ValueError("action reduction removed every feature; causal estimator requires a representation")
    est=OrthogonalTargetEstimator(folds=folds,seed=seed)
    full=est.fit(x,treatment,outcome)
    reduced=est.fit(x[:,indices],treatment,outcome)
    drift=float(reduced.target-full.target)
    scale=max(full.standard_error,1e-15)
    return ActionToCausalMismatchAudit(
        cert,full,reduced,drift,abs(drift)/scale,bool(cert.action_invariant and (cert.observed_action_changes or 0)==0),False,
        "ACTION_CERTIFICATE_NOT_PROMOTED_TO_CAUSAL_CERTIFICATE",
    )

# Thin standardized entry points for the remaining certificate families.
def certify_markov_dynamics(transition_matrix,partition,**kwargs)->LumpabilityCertificate:
    return audit_lumpability(transition_matrix,partition,**kwargs)

def certify_decision_compression(beliefs,state_action_utilities,*,maximum_regret:float,**kwargs)->BeliefCompressionResult:
    return compress_beliefs(beliefs,state_action_utilities,maximum_regret=maximum_regret,**kwargs)

def certify_predictive_state(sequence,*,history_length:int,probability_tolerance:float,smoothing:float=.5)->PredictiveStateResult:
    return discover_predictive_states(sequence,history_length=history_length,probability_tolerance=probability_tolerance,smoothing=smoothing)
