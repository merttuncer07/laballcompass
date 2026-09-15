import json

import numpy as np

from capl import learn_portfolio_policy


rng = np.random.default_rng(41)
training_features = rng.normal(size=(240, 2))
validation_features = rng.normal(size=(500, 2))

def make_returns(features):
    predictable = np.column_stack((
        .012 * features[:, 0],
        -.012 * features[:, 0],
        .010 * features[:, 1],
    ))
    return .0015 + predictable + rng.normal(scale=.004, size=predictable.shape)

result = learn_portfolio_policy(
    training_features, make_returns(training_features),
    validation_features, make_returns(validation_features),
    maximum_asset_weight=.70,
    maximum_turnover=.40,
    risk_aversion=2.0,
    transaction_cost=.0002,
    population_size=80,
    generations=30,
    seed=4,
)
print(json.dumps({
    "training_objective": result.training_metrics.objective,
    "validation_mean_return": result.validation_metrics.mean_return,
    "validation_volatility": result.validation_metrics.return_volatility,
    "validation_certainty_equivalent": result.validation_metrics.certainty_equivalent,
    "equal_weight_certainty_equivalent": result.equal_weight_validation_metrics.certainty_equivalent,
    "objective_improvement": result.validation_objective_improvement_vs_equal_weight,
    "average_turnover": result.validation_metrics.average_turnover,
    "maximum_realized_turnover": result.validation_action_audit.maximum_realized_turnover,
    "maximum_realized_weight": result.validation_action_audit.maximum_weight,
    "violations": {
        "sum": result.validation_action_audit.sum_violations,
        "lower": result.validation_action_audit.lower_bound_violations,
        "upper": result.validation_action_audit.upper_bound_violations,
        "turnover": result.validation_action_audit.turnover_violations,
    },
    "candidates_evaluated": result.candidates_evaluated,
    "status": result.status,
}, indent=2))
