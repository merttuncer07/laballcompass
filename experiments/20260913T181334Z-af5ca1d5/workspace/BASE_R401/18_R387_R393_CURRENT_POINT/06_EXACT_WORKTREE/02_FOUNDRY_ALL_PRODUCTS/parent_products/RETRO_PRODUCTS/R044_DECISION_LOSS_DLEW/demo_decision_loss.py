import json

import numpy as np

from dlew import evaluate_decision_models


rng = np.random.default_rng(44)

def sample(size):
    common = .001 + rng.normal(scale=.002, size=size)
    spread = rng.normal(scale=.010, size=size)
    outcomes = np.column_stack((common + spread, common - spread))
    lowest_rmse = outcomes + rng.normal(scale=.006, size=outcomes.shape)
    common_bias = rng.normal(loc=.030, scale=.003, size=(size, 1))
    decision_boundary = outcomes + common_bias + rng.normal(scale=.001, size=outcomes.shape)
    return outcomes, {"lowest_rmse": lowest_rmse, "decision_boundary": decision_boundary}

training_outcomes, training_predictions = sample(500)
validation_outcomes, validation_predictions = sample(1000)
result = evaluate_decision_models(
    training_predictions, training_outcomes,
    validation_predictions, validation_outcomes,
    [[1, 0], [0, 1]],
    initial_action_exposure=[.5, .5],
    transaction_cost=.0002,
)

print(json.dumps({
    "selected_by_prediction_rmse": result.selected_by_training_prediction_rmse,
    "selected_by_decision_loss": result.selected_by_training_decision_loss,
    "ranking_diverges": result.selection_ranking_diverges,
    "validation": {
        candidate.name: {
            "prediction_rmse": candidate.prediction_rmse,
            "mean_realized_payoff": candidate.mean_realized_payoff,
            "mean_decision_regret": candidate.mean_decision_regret,
            "oracle_action_agreement": candidate.action_agreement_with_oracle,
            "total_turnover": candidate.total_turnover,
        }
        for candidate in result.validation_candidates
    },
    "validation_regret_reduction": result.validation_regret_reduction_from_decision_selection,
    "status": result.status,
}, indent=2))
