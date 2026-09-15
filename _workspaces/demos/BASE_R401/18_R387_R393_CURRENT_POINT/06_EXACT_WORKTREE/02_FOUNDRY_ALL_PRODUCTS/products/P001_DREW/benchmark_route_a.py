"""Adverse-shift benchmark for DREW v0.1.

Search data contains an adaptive decoy that is excellent in-sample and fails after selection.
Validation is used to audit/correct the search; a fresh final segment measures the corrected choice.
"""
import json
import time

import numpy as np

if __package__:
    from .drew import audit_decision_model_selection, decision_regret_matrix
else:
    from drew import audit_decision_model_selection, decision_regret_matrix
if __package__:
    from .parents.dlew import evaluate_decision_models
else:
    from parents.dlew import evaluate_decision_models


def make_segment(rng, n, decoy_mode="good"):
    common = .001 + rng.normal(scale=.002, size=n)
    spread = rng.normal(scale=.010, size=n)
    y = np.column_stack((common + spread, common - spread))

    low_rmse = y + rng.normal(scale=.006, size=y.shape)
    common_bias = rng.normal(loc=.030, scale=.003, size=(n, 1))
    stable_decision = y + common_bias + rng.normal(scale=.001, size=y.shape)
    if decoy_mode == "good":
        adaptive_decoy = y + rng.normal(scale=.00025, size=y.shape)
    elif decoy_mode == "bad":
        adaptive_decoy = y[:, ::-1] + rng.normal(scale=.00025, size=y.shape)
    else:
        raise ValueError(decoy_mode)
    return y, {
        "adaptive_decoy": adaptive_decoy,
        "low_rmse": low_rmse,
        "stable_decision": stable_decision,
    }


def mean_regret_for(name, predictions, outcomes):
    names, matrix = decision_regret_matrix(
        predictions, outcomes, [[1, 0], [0, 1]],
        initial_action_exposure=[.5, .5], transaction_cost=.0002,
    )
    return float(matrix[:, names.index(name)].mean())


def run(seed=20260825):
    rng = np.random.default_rng(seed)
    search_y, search_p = make_segment(rng, 500, "good")
    validation_y, validation_p = make_segment(rng, 900, "bad")
    final_y, final_p = make_segment(rng, 1200, "bad")

    t0 = time.perf_counter()
    dlew = evaluate_decision_models(
        search_p, search_y, validation_p, validation_y, [[1, 0], [0, 1]],
        initial_action_exposure=[.5, .5], transaction_cost=.0002,
    )
    dlew_seconds = time.perf_counter() - t0

    t1 = time.perf_counter()
    drew = audit_decision_model_selection(
        search_p, search_y, validation_p, validation_y, [[1, 0], [0, 1]],
        initial_action_exposure=[.5, .5], transaction_cost=.0002,
        bootstrap_samples=500, random_seed=11, material_regret=1e-5,
    )
    drew_seconds = time.perf_counter() - t1

    rmse_selected = dlew.selected_by_training_prediction_rmse
    decision_selected = dlew.selected_by_training_decision_loss
    validation_corrected = drew.protected_best_candidate
    final_regrets = {
        "train_rmse_selected": mean_regret_for(rmse_selected, final_p, final_y),
        "train_decision_selected": mean_regret_for(decision_selected, final_p, final_y),
        "validation_corrected": mean_regret_for(validation_corrected, final_p, final_y),
    }
    decoy_regret = final_regrets["train_decision_selected"]
    corrected = final_regrets["validation_corrected"]
    reduction = 0.0 if decoy_regret <= 1e-15 else 1.0 - corrected / decoy_regret

    return {
        "seed": seed,
        "search_rows": len(search_y),
        "validation_rows": len(validation_y),
        "fresh_final_rows": len(final_y),
        "baseline_train_rmse_selected": rmse_selected,
        "dlew_train_decision_selected": decision_selected,
        "drew_protected_best_candidate": validation_corrected,
        "adaptive_selection_status": drew.adaptive_selection.status,
        "adaptive_selection_protected_regret": drew.adaptive_selection.selected_holdout_regret,
        "final_mean_decision_regret": final_regrets,
        "final_regret_reduction_vs_train_decision_selection": reduction,
        "dlew_seconds": dlew_seconds,
        "drew_seconds": drew_seconds,
        "status": drew.status,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
