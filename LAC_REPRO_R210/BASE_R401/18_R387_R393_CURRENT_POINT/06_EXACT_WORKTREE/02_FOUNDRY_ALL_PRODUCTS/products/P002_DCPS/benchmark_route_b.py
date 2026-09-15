import json
import time
import numpy as np

if __package__:
    from .dcps import (
        build_decision_closed_representation,
        learn_constrained_policy_from_representation,
        evaluate_representation_predictors,
    )
else:
    from dcps import (
        build_decision_closed_representation,
        learn_constrained_policy_from_representation,
        evaluate_representation_predictors,
    )
if __package__:
    from .parents.capl import learn_portfolio_policy
else:
    from parents.capl import learn_portfolio_policy

SAFE = {(0, 0): .10, (0, 1): .80, (1, 0): .20, (1, 1): .90}
INCOMPATIBLE = {(0, 0): .10, (0, 1): .20, (1, 0): .80, (1, 1): .90}
UTILITIES = np.eye(2)


def sequence(prob_one, seed, length):
    rng = np.random.default_rng(seed)
    values = [0, 1]
    for _ in range(length - 2):
        values.append(int(rng.random() < prob_one[(values[-2], values[-1])]))
    return values


def returns(values, seed):
    rng = np.random.default_rng(seed)
    symbols = np.asarray(values)
    base = np.where(symbols[:, None] == np.array([0, 1])[None, :], .012, -.003)
    return base + rng.normal(scale=.003, size=base.shape)


def raw_context_features(values):
    contexts = [(0, 0), (0, 1), (1, 0), (1, 1)]
    index = {context: i for i, context in enumerate(contexts)}
    result = []
    for t in range(2, len(values)):
        row = np.zeros(4)
        row[index[(values[t - 2], values[t - 1])]] = 1.0
        result.append(row)
    return np.asarray(result)


def direct_bit_features(values):
    return np.asarray([[values[t - 2], values[t - 1]] for t in range(2, len(values))], dtype=float)


def policy_summary(result):
    return {
        "validation_objective": result.validation_metrics.objective,
        "validation_mean_return": result.validation_metrics.mean_return,
        "validation_volatility": result.validation_metrics.return_volatility,
        "improvement_vs_equal_weight": result.validation_objective_improvement_vs_equal_weight,
        "coefficient_rows": len(result.coefficients),
        "constraint_violations": {
            "sum": result.validation_action_audit.sum_violations,
            "lower": result.validation_action_audit.lower_bound_violations,
            "upper": result.validation_action_audit.upper_bound_violations,
            "turnover": result.validation_action_audit.turnover_violations,
        },
    }


def run():
    safe_rep = build_decision_closed_representation(
        sequence(SAFE, 1, 20000), UTILITIES,
        history_length=2, probability_tolerance=.035, maximum_decision_regret=0,
    )
    incompatible_rep = build_decision_closed_representation(
        sequence(INCOMPATIBLE, 2, 20000), UTILITIES,
        history_length=2, probability_tolerance=.035, maximum_decision_regret=0,
    )

    train_seq = sequence(SAFE, 3, 600)
    val_seq = sequence(SAFE, 4, 900)
    train_returns = returns(train_seq, 5)
    val_returns = returns(val_seq, 6)
    settings = dict(
        maximum_asset_weight=.9, maximum_turnover=.8, risk_aversion=2,
        transaction_cost=.0002, population_size=20, generations=5, seed=4,
    )
    t0 = time.perf_counter()
    dcps_policy = learn_constrained_policy_from_representation(
        safe_rep, train_seq, train_returns, val_seq, val_returns, **settings
    )
    dcps_seconds = time.perf_counter() - t0
    raw_policy = learn_portfolio_policy(
        raw_context_features(train_seq), train_returns[2:],
        raw_context_features(val_seq), val_returns[2:], **settings
    )
    direct_policy = learn_portfolio_policy(
        direct_bit_features(train_seq), train_returns[2:],
        direct_bit_features(val_seq), val_returns[2:], **settings
    )
    memoryless_policy = learn_portfolio_policy(
        np.empty((len(train_seq) - 2, 0)), train_returns[2:],
        np.empty((len(val_seq) - 2, 0)), val_returns[2:], **settings
    )

    fit_seq = sequence(SAFE, 7, 1800)
    selection_seq = sequence(SAFE, 8, 900)
    final_seq = sequence(SAFE, 9, 1200)
    dlew = evaluate_representation_predictors(
        safe_rep,
        fit_seq, returns(fit_seq, 10),
        selection_seq, returns(selection_seq, 11),
        final_seq, returns(final_seq, 12),
        [[1, 0], [0, 1]], initial_action_exposure=[.5, .5], transaction_cost=.0001,
    )
    validation_metrics = {
        item.name: {
            "rmse": item.prediction_rmse,
            "decision_regret": item.mean_decision_regret,
            "oracle_action_agreement": item.action_agreement_with_oracle,
        }
        for item in dlew.decision_loss.validation_candidates
    }
    return {
        "safe_merge": {
            "psct_states": safe_rep.predictive_state_result.predictive_state_count,
            "dsbc_clusters_before_closure": safe_rep.initial_decision_cluster_count,
            "decision_closed_clusters": safe_rep.decision_closed_cluster_count,
            "closure_refinement_splits": safe_rep.closure_refinement_splits,
            "status": safe_rep.status,
        },
        "dynamically_incompatible_merge": {
            "psct_states": incompatible_rep.predictive_state_result.predictive_state_count,
            "dsbc_clusters_before_closure": incompatible_rep.initial_decision_cluster_count,
            "decision_closed_clusters": incompatible_rep.decision_closed_cluster_count,
            "closure_refinement_splits": incompatible_rep.closure_refinement_splits,
            "status": incompatible_rep.status,
        },
        "capl_policy_comparison": {
            "decision_closed_2state": policy_summary(dcps_policy),
            "raw_context_4state": policy_summary(raw_policy),
            "direct_two_bit": policy_summary(direct_policy),
            "memoryless": policy_summary(memoryless_policy),
            "dcps_seconds": dcps_seconds,
        },
        "dlew_representation_comparison": {
            "selected_by_prediction_rmse": dlew.decision_loss.selected_by_training_prediction_rmse,
            "selected_by_decision_loss": dlew.decision_loss.selected_by_training_decision_loss,
            "ranking_diverges": dlew.decision_loss.selection_ranking_diverges,
            "validation": validation_metrics,
            "fallback_status": dlew.status,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
