"""Decision-Loss Evaluation Workbench (DLEW) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class CandidateDecisionMetrics:
    name: str
    prediction_rmse: float
    mean_realized_payoff: float
    mean_oracle_payoff_given_previous_action: float
    mean_decision_regret: float
    total_turnover: float
    action_agreement_with_oracle: float
    actions: tuple[int, ...]


@dataclass(frozen=True)
class DecisionLossWorkbenchResult:
    selected_by_training_decision_loss: str
    selected_by_training_prediction_rmse: str
    selection_ranking_diverges: bool
    training_candidates: tuple[CandidateDecisionMetrics, ...]
    validation_candidates: tuple[CandidateDecisionMetrics, ...]
    selected_validation_decision_regret: float
    prediction_selected_validation_decision_regret: float
    validation_regret_reduction_from_decision_selection: float
    transaction_cost: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _evaluate(
    name: str,
    predictions: np.ndarray,
    outcomes: np.ndarray,
    actions: np.ndarray,
    initial_action: np.ndarray,
    transaction_cost: float,
) -> CandidateDecisionMetrics:
    previous = initial_action.copy()
    selected_actions: list[int] = []
    realized_payoffs: list[float] = []
    oracle_payoffs: list[float] = []
    regrets: list[float] = []
    oracle_agreement: list[float] = []
    total_turnover = 0.0
    for prediction, outcome in zip(predictions, outcomes):
        predicted_net = actions @ prediction - transaction_cost * np.sum(np.abs(actions - previous), axis=1)
        selected = int(np.argmax(predicted_net))
        actual_net = actions @ outcome - transaction_cost * np.sum(np.abs(actions - previous), axis=1)
        oracle = int(np.argmax(actual_net))
        realized = float(actual_net[selected])
        oracle_value = float(actual_net[oracle])
        turnover = float(np.sum(np.abs(actions[selected] - previous)))
        selected_actions.append(selected)
        realized_payoffs.append(realized)
        oracle_payoffs.append(oracle_value)
        regrets.append(oracle_value - realized)
        oracle_agreement.append(float(selected == oracle))
        total_turnover += turnover
        previous = actions[selected]
    return CandidateDecisionMetrics(
        name=name,
        prediction_rmse=float(np.sqrt(np.mean((predictions - outcomes) ** 2))),
        mean_realized_payoff=float(np.mean(realized_payoffs)),
        mean_oracle_payoff_given_previous_action=float(np.mean(oracle_payoffs)),
        mean_decision_regret=float(np.mean(regrets)),
        total_turnover=total_turnover,
        action_agreement_with_oracle=float(np.mean(oracle_agreement)),
        actions=tuple(selected_actions),
    )


def evaluate_decision_models(
    training_predictions: Mapping[str, Sequence[Sequence[float]]],
    training_outcomes: Sequence[Sequence[float]],
    validation_predictions: Mapping[str, Sequence[Sequence[float]]],
    validation_outcomes: Sequence[Sequence[float]],
    action_payoff_exposures: Sequence[Sequence[float]],
    *,
    initial_action_exposure: Sequence[float],
    transaction_cost: float = 0.0,
) -> DecisionLossWorkbenchResult:
    """Select prediction models by the downstream decisions they induce."""

    train_y = np.asarray(training_outcomes, dtype=float)
    val_y = np.asarray(validation_outcomes, dtype=float)
    actions = np.asarray(action_payoff_exposures, dtype=float)
    initial = np.asarray(initial_action_exposure, dtype=float)
    if train_y.ndim != 2 or val_y.ndim != 2 or actions.ndim != 2:
        raise ValueError("outcomes and action exposures must be matrices")
    if train_y.shape[1] != val_y.shape[1] or actions.shape[1] != train_y.shape[1] or initial.shape != (train_y.shape[1],):
        raise ValueError("outcome and action exposure dimensions must match")
    if min(train_y.shape[0], val_y.shape[0]) < 2 or actions.shape[0] < 2:
        raise ValueError("at least two samples and two actions are required")
    if transaction_cost < 0 or not all(np.all(np.isfinite(v)) for v in (train_y, val_y, actions, initial)):
        raise ValueError("values must be finite and transaction cost nonnegative")
    names = sorted(training_predictions)
    if not names or set(names) != set(validation_predictions):
        raise ValueError("training and validation candidate names must match and be nonempty")

    train_results = []
    validation_results = []
    for name in names:
        train_prediction = np.asarray(training_predictions[name], dtype=float)
        val_prediction = np.asarray(validation_predictions[name], dtype=float)
        if train_prediction.shape != train_y.shape or val_prediction.shape != val_y.shape:
            raise ValueError(f"prediction shape mismatch for {name}")
        if not np.all(np.isfinite(train_prediction)) or not np.all(np.isfinite(val_prediction)):
            raise ValueError("predictions must be finite")
        train_results.append(_evaluate(name, train_prediction, train_y, actions, initial, transaction_cost))
        validation_results.append(_evaluate(name, val_prediction, val_y, actions, initial, transaction_cost))
    decision_selected = min(train_results, key=lambda item: (item.mean_decision_regret, -item.mean_realized_payoff, item.name)).name
    prediction_selected = min(train_results, key=lambda item: (item.prediction_rmse, item.name)).name
    validation_by_name = {item.name: item for item in validation_results}
    decision_regret = validation_by_name[decision_selected].mean_decision_regret
    prediction_regret = validation_by_name[prediction_selected].mean_decision_regret
    return DecisionLossWorkbenchResult(
        selected_by_training_decision_loss=decision_selected,
        selected_by_training_prediction_rmse=prediction_selected,
        selection_ranking_diverges=decision_selected != prediction_selected,
        training_candidates=tuple(train_results),
        validation_candidates=tuple(validation_results),
        selected_validation_decision_regret=decision_regret,
        prediction_selected_validation_decision_regret=prediction_regret,
        validation_regret_reduction_from_decision_selection=float(prediction_regret - decision_regret),
        transaction_cost=float(transaction_cost),
        status="DECISION_AND_PREDICTION_SELECTION_DIVERGE" if decision_selected != prediction_selected else "DECISION_AND_PREDICTION_SELECTION_AGREE",
    )
