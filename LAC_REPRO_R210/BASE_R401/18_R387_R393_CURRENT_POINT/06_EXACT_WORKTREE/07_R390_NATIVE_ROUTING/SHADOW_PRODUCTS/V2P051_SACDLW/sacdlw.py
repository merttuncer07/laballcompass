"""V2P051 SACDLW shadow candidate.

Composition: R037 SACPS -> R044 DLEW.
SACPS support-aware covariance enters DLEW's finite-action utility before
argmax selection. The removal control keeps the DLEW shell fixed and replaces
only the support-aware covariance with the raw sample covariance.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence
import numpy as np


@dataclass(frozen=True)
class RiskDecisionMetrics:
    name: str
    prediction_rmse: float
    mean_realized_reference_utility: float
    mean_oracle_reference_utility_given_previous_action: float
    mean_reference_decision_regret: float
    total_turnover: float
    action_agreement_with_reference_oracle: float
    actions: tuple[int, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _quadratic_action_risk(actions: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    return np.einsum("ij,jk,ik->i", actions, covariance, actions)


def _evaluate(
    name: str,
    predictions: np.ndarray,
    outcomes: np.ndarray,
    actions: np.ndarray,
    initial_action: np.ndarray,
    transaction_cost: float,
    risk_aversion: float,
    decision_covariance: np.ndarray,
    reference_covariance: np.ndarray,
) -> RiskDecisionMetrics:
    previous = initial_action.copy()
    selected_actions: list[int] = []
    realized_utilities: list[float] = []
    oracle_utilities: list[float] = []
    regrets: list[float] = []
    oracle_agreement: list[float] = []
    total_turnover = 0.0
    decision_risk = _quadratic_action_risk(actions, decision_covariance)
    reference_risk = _quadratic_action_risk(actions, reference_covariance)
    for prediction, outcome in zip(predictions, outcomes):
        turnover = np.sum(np.abs(actions - previous), axis=1)
        predicted_utility = (
            actions @ prediction
            - transaction_cost * turnover
            - risk_aversion * decision_risk
        )
        selected = int(np.argmax(predicted_utility))
        actual_reference_utility = (
            actions @ outcome
            - transaction_cost * turnover
            - risk_aversion * reference_risk
        )
        oracle = int(np.argmax(actual_reference_utility))
        realized = float(actual_reference_utility[selected])
        oracle_value = float(actual_reference_utility[oracle])
        selected_actions.append(selected)
        realized_utilities.append(realized)
        oracle_utilities.append(oracle_value)
        regrets.append(oracle_value - realized)
        oracle_agreement.append(float(selected == oracle))
        total_turnover += float(turnover[selected])
        previous = actions[selected]
    return RiskDecisionMetrics(
        name=name,
        prediction_rmse=float(np.sqrt(np.mean((predictions - outcomes) ** 2))),
        mean_realized_reference_utility=float(np.mean(realized_utilities)),
        mean_oracle_reference_utility_given_previous_action=float(np.mean(oracle_utilities)),
        mean_reference_decision_regret=float(np.mean(regrets)),
        total_turnover=float(total_turnover),
        action_agreement_with_reference_oracle=float(np.mean(oracle_agreement)),
        actions=tuple(selected_actions),
    )


def _validate_matrix(name: str, value, *, columns: int | None = None, minimum_rows: int = 2) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[0] < minimum_rows or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite matrix with at least {minimum_rows} rows")
    if columns is not None and array.shape[1] != columns:
        raise ValueError(f"{name} column count must match the decision dimension")
    return array


def support_covariance_decision_loss_workbench(
    dlew_module,
    covariance_estimator,
    training_predictions: Mapping[str, Sequence[Sequence[float]]],
    training_outcomes: Sequence[Sequence[float]],
    validation_predictions: Mapping[str, Sequence[Sequence[float]]],
    validation_outcomes: Sequence[Sequence[float]],
    action_payoff_exposures: Sequence[Sequence[float]],
    risk_training_returns: Sequence[Sequence[float]],
    risk_validation_returns: Sequence[Sequence[float]],
    support_mask: Sequence[Sequence[bool]],
    *,
    initial_action_exposure: Sequence[float],
    support_calibration_returns: Sequence[Sequence[float]] | None = None,
    shrinkage_grid: Sequence[float] = tuple(np.linspace(0.0, 1.0, 21)),
    risk_aversion: float = 0.0,
    transaction_cost: float = 0.0,
    maximum_calibration_off_support_correlation: float | None = None,
) -> dict:
    """Run DLEW under support-aware versus raw covariance decision geometry.

    Model selection uses training decision regret under each geometry. Validation
    compares both selected models and induced actions against one common
    reference covariance estimated only from the validation-risk sample.
    """
    train_y = _validate_matrix("training_outcomes", training_outcomes)
    dimension = train_y.shape[1]
    val_y = _validate_matrix("validation_outcomes", validation_outcomes, columns=dimension)
    actions = _validate_matrix("action_payoff_exposures", action_payoff_exposures, columns=dimension)
    if actions.shape[0] < 2:
        raise ValueError("at least two actions are required")
    initial = np.asarray(initial_action_exposure, dtype=float)
    if initial.shape != (dimension,) or not np.all(np.isfinite(initial)):
        raise ValueError("initial_action_exposure must match the decision dimension")
    if risk_aversion < 0 or transaction_cost < 0:
        raise ValueError("risk_aversion and transaction_cost must be nonnegative")
    risk_train = _validate_matrix("risk_training_returns", risk_training_returns, columns=dimension, minimum_rows=3)
    risk_val = _validate_matrix("risk_validation_returns", risk_validation_returns, columns=dimension, minimum_rows=3)
    support = np.asarray(support_mask, dtype=bool)
    if support.shape != (dimension, dimension) or not np.array_equal(support, support.T) or not np.all(np.diag(support)):
        raise ValueError("support_mask must be symmetric, square, and include the diagonal")
    calibration = None
    if support_calibration_returns is not None:
        calibration = _validate_matrix("support_calibration_returns", support_calibration_returns, columns=dimension, minimum_rows=5)
    if maximum_calibration_off_support_correlation is not None:
        limit = float(maximum_calibration_off_support_correlation)
        if not 0 <= limit <= 1:
            raise ValueError("maximum calibration off-support correlation must lie in [0,1]")
        if calibration is None:
            raise ValueError("support_calibration_returns are required for support contradiction routing")
        unsupported = np.logical_not(support).copy()
        np.fill_diagonal(unsupported, False)
        max_off_support = 0.0
        if np.any(unsupported):
            corr = np.corrcoef(calibration, rowvar=False)
            max_off_support = float(np.max(np.abs(corr[unsupported])))
            if max_off_support > limit:
                return {
                    "status": "ABSTAIN_SUPPORT_CONTRADICTED_BY_CALIBRATION",
                    "maximum_calibration_off_support_correlation": max_off_support,
                    "configured_off_support_correlation_limit": limit,
                    "fallback": "ordinary DLEW or an explicitly chosen raw-covariance risk control may be run by the caller; SACDLW does not silently alter the declared support",
                }

    names = sorted(training_predictions)
    if not names or set(names) != set(validation_predictions):
        raise ValueError("training and validation candidate names must match and be nonempty")
    train_predictions: dict[str, np.ndarray] = {}
    val_predictions: dict[str, np.ndarray] = {}
    for name in names:
        tr = np.asarray(training_predictions[name], dtype=float)
        va = np.asarray(validation_predictions[name], dtype=float)
        if tr.shape != train_y.shape or va.shape != val_y.shape or not np.all(np.isfinite(tr)) or not np.all(np.isfinite(va)):
            raise ValueError(f"prediction shape or finiteness mismatch for {name}")
        train_predictions[name] = tr
        val_predictions[name] = va

    estimate = covariance_estimator(
        risk_train,
        support,
        validation_returns=calibration,
        shrinkage_grid=shrinkage_grid,
    )
    supported_covariance = np.asarray(estimate.covariance, dtype=float)
    raw_covariance = np.cov(risk_train, rowvar=False, ddof=1)
    reference_covariance = np.cov(risk_val, rowvar=False, ddof=1)
    for covariance in (supported_covariance, raw_covariance, reference_covariance):
        if covariance.shape != (dimension, dimension) or not np.all(np.isfinite(covariance)):
            raise RuntimeError("covariance geometry is unavailable")

    candidate_train = [
        _evaluate(name, train_predictions[name], train_y, actions, initial, transaction_cost, risk_aversion,
                  supported_covariance, supported_covariance)
        for name in names
    ]
    control_train = [
        _evaluate(name, train_predictions[name], train_y, actions, initial, transaction_cost, risk_aversion,
                  raw_covariance, raw_covariance)
        for name in names
    ]
    candidate_selected = min(candidate_train, key=lambda row: (row.mean_reference_decision_regret, -row.mean_realized_reference_utility, row.name)).name
    control_selected = min(control_train, key=lambda row: (row.mean_reference_decision_regret, -row.mean_realized_reference_utility, row.name)).name

    candidate_validation = _evaluate(
        candidate_selected, val_predictions[candidate_selected], val_y, actions, initial,
        transaction_cost, risk_aversion, supported_covariance, reference_covariance,
    )
    control_validation = _evaluate(
        control_selected, val_predictions[control_selected], val_y, actions, initial,
        transaction_cost, risk_aversion, raw_covariance, reference_covariance,
    )

    parent = dlew_module.evaluate_decision_models(
        training_predictions, train_y, validation_predictions, val_y, actions,
        initial_action_exposure=initial, transaction_cost=transaction_cost,
    )
    raw_off_support = np.logical_not(support).copy()
    np.fill_diagonal(raw_off_support, False)
    raw_off_support_max = float(np.max(np.abs(raw_covariance[raw_off_support]))) if np.any(raw_off_support) else 0.0
    covariance_equal = bool(np.allclose(supported_covariance, raw_covariance, atol=1e-12, rtol=1e-12))
    candidate_actions_equal_control = candidate_validation.actions == control_validation.actions
    gain = float(control_validation.mean_reference_decision_regret - candidate_validation.mean_reference_decision_regret)
    return {
        "selected_shrinkage": float(estimate.selected_shrinkage),
        "risk_aversion": float(risk_aversion),
        "supported_covariance": supported_covariance.tolist(),
        "raw_covariance": raw_covariance.tolist(),
        "reference_validation_covariance": reference_covariance.tolist(),
        "raw_off_support_max_abs_covariance": raw_off_support_max,
        "candidate_selected_model": candidate_selected,
        "control_selected_model": control_selected,
        "parent_dlew_selected_model": parent.selected_by_training_decision_loss,
        "candidate_training_candidates": [row.to_dict() for row in candidate_train],
        "control_training_candidates": [row.to_dict() for row in control_train],
        "candidate_validation": candidate_validation.to_dict(),
        "control_validation": control_validation.to_dict(),
        "validation_reference_regret_gain_vs_raw_covariance": gain,
        "supported_equals_raw_covariance": covariance_equal,
        "candidate_actions_equal_control": candidate_actions_equal_control,
        "status": "SUPPORT_COVARIANCE_CHANGED_DLEW_DECISION_GEOMETRY" if (candidate_selected != control_selected or not candidate_actions_equal_control) else "SUPPORT_COVARIANCE_COLLAPSED_TO_RAW_DLEW_GEOMETRY",
    }
