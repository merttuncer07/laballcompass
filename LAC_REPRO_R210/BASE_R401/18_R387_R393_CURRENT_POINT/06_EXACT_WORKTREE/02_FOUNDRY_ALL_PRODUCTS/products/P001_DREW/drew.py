"""Decision Reliability Evaluation Workbench (DREW) v0.1.

Route-A composition of ACSA, DLEW, SCE, TDSX, MDDC and optional MIFF.
The workbench does not collapse heterogeneous diagnostics into a single pseudo-score.
It preserves each parent result, exposes directed adapters, and returns evidence flags.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np

if __package__:
    from .parents.acsa import SelectionAudit, audit_adaptive_selection
else:
    from parents.acsa import SelectionAudit, audit_adaptive_selection
if __package__:
    from .parents.dlew import DecisionLossWorkbenchResult, evaluate_decision_models
else:
    from parents.dlew import DecisionLossWorkbenchResult, evaluate_decision_models
if __package__:
    from .parents.mddc import DivergenceResult, diagnose_metric_decision_divergence
else:
    from parents.mddc import DivergenceResult, diagnose_metric_decision_divergence
if __package__:
    from .parents.miff import FirewallResult, InformationFlow, design_inference_firewall
else:
    from parents.miff import FirewallResult, InformationFlow, design_inference_firewall
if __package__:
    from .parents.sce import SpecificationCurve, run_specification_curve
else:
    from parents.sce import SpecificationCurve, run_specification_curve
if __package__:
    from .parents.tdsx import SensitivitySurface, explore_sensitivity_surface
else:
    from parents.tdsx import SensitivitySurface, explore_sensitivity_surface


@dataclass(frozen=True)
class DecisionSelectionAudit:
    candidate_names: tuple[str, ...]
    decision_loss: DecisionLossWorkbenchResult
    adaptive_selection: SelectionAudit
    selection_loss_matrix_means: tuple[float, ...]
    protected_loss_matrix_means: tuple[float, ...]
    decision_selector_matches_loss_matrix: bool
    protected_best_candidate: str
    status: str


@dataclass(frozen=True)
class ReliabilityWorkbenchResult:
    decision_audit: DecisionSelectionAudit | None
    specification_curve: SpecificationCurve | None
    sensitivity_surface: SensitivitySurface | None
    metric_decision_divergence: DivergenceResult | None
    inference_firewall: FirewallResult | None
    evidence_flags: tuple[str, ...]
    branch_coverage: tuple[str, ...]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_decision_arrays(
    predictions: Mapping[str, Sequence[Sequence[float]]],
    outcomes: Sequence[Sequence[float]],
    action_payoff_exposures: Sequence[Sequence[float]],
    initial_action_exposure: Sequence[float],
    transaction_cost: float,
) -> tuple[tuple[str, ...], np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    y = np.asarray(outcomes, dtype=float)
    actions = np.asarray(action_payoff_exposures, dtype=float)
    initial = np.asarray(initial_action_exposure, dtype=float)
    names = tuple(sorted(predictions))
    if not names:
        raise ValueError("at least one prediction candidate is required")
    if y.ndim != 2 or actions.ndim != 2 or y.shape[0] < 2 or actions.shape[0] < 2:
        raise ValueError("outcomes must have >=2 rows and actions must contain >=2 actions")
    if actions.shape[1] != y.shape[1] or initial.shape != (y.shape[1],):
        raise ValueError("outcome/action/initial exposure dimensions must match")
    if transaction_cost < 0:
        raise ValueError("transaction_cost must be nonnegative")
    arrays = {name: np.asarray(predictions[name], dtype=float) for name in names}
    if any(value.shape != y.shape for value in arrays.values()):
        raise ValueError("every prediction candidate must match the outcome matrix shape")
    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(actions)) or not np.all(np.isfinite(initial)):
        raise ValueError("outcomes and action exposures must be finite")
    if any(not np.all(np.isfinite(value)) for value in arrays.values()):
        raise ValueError("predictions must be finite")
    return names, y, actions, initial, arrays


def decision_regret_matrix(
    predictions: Mapping[str, Sequence[Sequence[float]]],
    outcomes: Sequence[Sequence[float]],
    action_payoff_exposures: Sequence[Sequence[float]],
    *,
    initial_action_exposure: Sequence[float],
    transaction_cost: float = 0.0,
) -> tuple[tuple[str, ...], np.ndarray]:
    """Convert raw candidate predictions into case-by-candidate downstream decision regret.

    This is the principal DLEW -> ACSA adapter.  Each candidate follows its own sequential
    previous-action path, matching DLEW's transaction-cost semantics.  Lower loss is better.
    """
    names, y, actions, initial, arrays = _validate_decision_arrays(
        predictions, outcomes, action_payoff_exposures, initial_action_exposure, transaction_cost
    )
    losses = np.empty((y.shape[0], len(names)), dtype=float)
    for column, name in enumerate(names):
        previous = initial.copy()
        for row, (prediction, outcome) in enumerate(zip(arrays[name], y)):
            predicted_net = actions @ prediction - transaction_cost * np.sum(np.abs(actions - previous), axis=1)
            selected = int(np.argmax(predicted_net))
            actual_net = actions @ outcome - transaction_cost * np.sum(np.abs(actions - previous), axis=1)
            oracle = int(np.argmax(actual_net))
            losses[row, column] = float(actual_net[oracle] - actual_net[selected])
            previous = actions[selected]
    return names, losses


def audit_decision_model_selection(
    training_predictions: Mapping[str, Sequence[Sequence[float]]],
    training_outcomes: Sequence[Sequence[float]],
    validation_predictions: Mapping[str, Sequence[Sequence[float]]],
    validation_outcomes: Sequence[Sequence[float]],
    action_payoff_exposures: Sequence[Sequence[float]],
    *,
    initial_action_exposure: Sequence[float],
    transaction_cost: float = 0.0,
    bootstrap_samples: int = 1000,
    random_seed: int = 0,
    material_regret: float = 0.0,
) -> DecisionSelectionAudit:
    """Select by DLEW decision loss, then audit that adaptive selection on protected data with ACSA."""
    decision = evaluate_decision_models(
        training_predictions,
        training_outcomes,
        validation_predictions,
        validation_outcomes,
        action_payoff_exposures,
        initial_action_exposure=initial_action_exposure,
        transaction_cost=transaction_cost,
    )
    train_names, train_losses = decision_regret_matrix(
        training_predictions,
        training_outcomes,
        action_payoff_exposures,
        initial_action_exposure=initial_action_exposure,
        transaction_cost=transaction_cost,
    )
    val_names, val_losses = decision_regret_matrix(
        validation_predictions,
        validation_outcomes,
        action_payoff_exposures,
        initial_action_exposure=initial_action_exposure,
        transaction_cost=transaction_cost,
    )
    if train_names != val_names:
        raise ValueError("training and validation candidate names must match")
    adaptive = audit_adaptive_selection(
        train_losses,
        val_losses,
        candidate_names=train_names,
        bootstrap_samples=bootstrap_samples,
        random_seed=random_seed,
        material_regret=material_regret,
    )
    matrix_selected = train_names[int(np.argmin(train_losses.mean(axis=0)))]
    matches = decision.selected_by_training_decision_loss == matrix_selected
    if adaptive.status == "ADAPTIVE_SELECTION_REGRET_DETECTED":
        status = "DECISION_SELECTION_FAILS_PROTECTED_AUDIT"
    elif not matches:
        status = "DLEW_TIEBREAK_DIFFERS_FROM_MEAN_REGRET_MATRIX"
    else:
        status = "DECISION_SELECTION_SURVIVES_PROTECTED_AUDIT"
    return DecisionSelectionAudit(
        candidate_names=train_names,
        decision_loss=decision,
        adaptive_selection=adaptive,
        selection_loss_matrix_means=tuple(map(float, train_losses.mean(axis=0))),
        protected_loss_matrix_means=tuple(map(float, val_losses.mean(axis=0))),
        decision_selector_matches_loss_matrix=matches,
        protected_best_candidate=adaptive.holdout_best_candidate,
        status=status,
    )


def explore_decision_selection_surface(
    scenario_builder: Callable[[Mapping[str, float]], Mapping[str, Any]],
    parameter_grids: Mapping[str, Sequence[float]],
    baseline_parameters: Mapping[str, float],
    *,
    maximum_points: int = 200_000,
) -> SensitivitySurface:
    """TDSX -> DLEW adapter: find where decision-loss selection stops beating RMSE selection.

    ``scenario_builder(params)`` must return keyword arguments accepted by
    :func:`evaluate_decision_models`, including ``initial_action_exposure``.
    The explored metric is validation regret reduction from decision-aware selection; zero is the
    decision boundary.
    """
    def evaluator(params: Mapping[str, float]) -> float:
        scenario = dict(scenario_builder(params))
        result = evaluate_decision_models(**scenario)
        return float(result.validation_regret_reduction_from_decision_selection)

    return explore_sensitivity_surface(
        evaluator,
        parameter_grids,
        baseline_parameters,
        decision_threshold=0.0,
        decision_direction="ABOVE",
        maximum_points=maximum_points,
    )


def _coerce_flows(flows: Sequence[InformationFlow | Mapping[str, Any]]) -> tuple[InformationFlow, ...]:
    converted = []
    for flow in flows:
        converted.append(flow if isinstance(flow, InformationFlow) else InformationFlow(**dict(flow)))
    return tuple(converted)


def run_reliability_workbench(
    *,
    decision_inputs: Mapping[str, Any] | None = None,
    specification_inputs: Mapping[str, Any] | None = None,
    sensitivity_inputs: Mapping[str, Any] | None = None,
    divergence_inputs: Mapping[str, Any] | None = None,
    firewall_inputs: Mapping[str, Any] | None = None,
) -> ReliabilityWorkbenchResult:
    """Execute any declared Route-A branches and preserve their native result objects.

    No heterogeneous diagnostics are averaged into a single score.  Evidence flags are routing
    signals for review/redesign, not automatic rejection rules.
    """
    if not any(x is not None for x in (decision_inputs, specification_inputs, sensitivity_inputs, divergence_inputs, firewall_inputs)):
        raise ValueError("at least one workbench branch must be supplied")

    decision = audit_decision_model_selection(**dict(decision_inputs)) if decision_inputs is not None else None
    specification = run_specification_curve(**dict(specification_inputs)) if specification_inputs is not None else None
    sensitivity = explore_sensitivity_surface(**dict(sensitivity_inputs)) if sensitivity_inputs is not None else None
    divergence = diagnose_metric_decision_divergence(**dict(divergence_inputs)) if divergence_inputs is not None else None
    firewall = None
    if firewall_inputs is not None:
        fw = dict(firewall_inputs)
        fw["flows"] = _coerce_flows(fw["flows"])
        firewall = design_inference_firewall(**fw)

    flags: list[str] = []
    coverage: list[str] = []
    if decision is not None:
        coverage.append("DECISION_SELECTION_AUDIT")
        if decision.decision_loss.selection_ranking_diverges:
            flags.append("PREDICTION_VS_DECISION_RANKING_DIVERGENCE")
        if decision.adaptive_selection.status == "ADAPTIVE_SELECTION_REGRET_DETECTED":
            flags.append("ADAPTIVE_SELECTION_HOLDOUT_REGRET")
        if decision.adaptive_selection.selection_fragility > 0.5:
            flags.append("SELECTION_BOOTSTRAP_FRAGILITY")
    if specification is not None:
        coverage.append("SPECIFICATION_CURVE")
        if specification.invalid_specifications:
            flags.append("INVALID_DECLARED_SPECIFICATIONS_PRESENT")
        if specification.sign_stable is False:
            flags.append("SPECIFICATION_SIGN_INSTABILITY")
    if sensitivity is not None:
        coverage.append("SENSITIVITY_SURFACE")
        if sensitivity.tipping_point is not None:
            flags.append("DECISION_TIPPING_POINT_INSIDE_DECLARED_SURFACE")
    if divergence is not None:
        coverage.append("METRIC_DECISION_DIVERGENCE")
        if divergence.ranking_inversions:
            flags.append("METRIC_DECISION_RANKING_INVERSION")
    if firewall is not None:
        coverage.append("INFERENCE_FIREWALL")
        if firewall.exposed_paths:
            flags.append("SUSPECT_TO_PROTECTED_INFORMATION_PATH_EXISTS")
        if firewall.cut_edges:
            flags.append("PROTECTED_EVALUATION_REQUIRES_FLOW_CUT")

    expected = {
        "DECISION_SELECTION_AUDIT", "SPECIFICATION_CURVE", "SENSITIVITY_SURFACE",
        "METRIC_DECISION_DIVERGENCE", "INFERENCE_FIREWALL",
    }
    full = set(coverage) == expected
    if flags:
        status = "FULL_ROUTE_A_WITH_REVIEW_FLAGS" if full else "PARTIAL_ROUTE_A_WITH_REVIEW_FLAGS"
    else:
        status = "FULL_ROUTE_A_NO_DECLARED_FLAGS" if full else "PARTIAL_ROUTE_A_NO_DECLARED_FLAGS"
    return ReliabilityWorkbenchResult(
        decision_audit=decision,
        specification_curve=specification,
        sensitivity_surface=sensitivity,
        metric_decision_divergence=divergence,
        inference_firewall=firewall,
        evidence_flags=tuple(flags),
        branch_coverage=tuple(coverage),
        status=status,
    )
