"""Real-data pilot: scikit-learn handwritten digits dataset.

Models are fit on one segment, compared on a search/selection segment, audited on a protected
validation segment, and checked on a fresh final segment.  No seed search is performed: the fixed
seed is 20260825.
"""
from __future__ import annotations

import json
import time

import numpy as np
from sklearn.datasets import load_digits
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

if __package__:
    from .drew import audit_decision_model_selection, decision_regret_matrix
else:
    from drew import audit_decision_model_selection, decision_regret_matrix


def one_hot(y: np.ndarray, classes: int = 10) -> np.ndarray:
    result = np.zeros((len(y), classes), dtype=float)
    result[np.arange(len(y)), y.astype(int)] = 1.0
    return result


def aligned_probability(model, x: np.ndarray, classes: int = 10) -> np.ndarray:
    raw = model.predict_proba(x)
    result = np.zeros((len(x), classes), dtype=float)
    result[:, np.asarray(model.classes_, dtype=int)] = raw
    return result


def run(seed: int = 20260825) -> dict:
    x, y = load_digits(return_X_y=True)
    x_fit, x_rest, y_fit, y_rest = train_test_split(
        x, y, test_size=.55, random_state=seed, stratify=y
    )
    x_search, x_rest, y_search, y_rest = train_test_split(
        x_rest, y_rest, test_size=40/55, random_state=seed + 1, stratify=y_rest
    )
    x_protected, x_final, y_protected, y_final = train_test_split(
        x_rest, y_rest, test_size=.5, random_state=seed + 2, stratify=y_rest
    )

    models = {}
    for c in [.003, .01, .03, .1, .3, 1, 3, 10, 30]:
        models[f"logreg_C{c}"] = make_pipeline(
            StandardScaler(), LogisticRegression(C=c, max_iter=3000, solver="lbfgs")
        )
    for k in [1, 3, 5, 7, 11, 17, 25]:
        models[f"knn_k{k}"] = KNeighborsClassifier(
            n_neighbors=k, weights="distance" if k in [7, 17] else "uniform"
        )
    for depth in [2, 3, 4, 5, 6, 8, None]:
        models[f"tree_d{depth}"] = DecisionTreeClassifier(max_depth=depth, random_state=seed)
    for estimators, depth in [(50, 5), (50, None), (100, 8), (100, None)]:
        models[f"rf_{estimators}_d{depth}"] = RandomForestClassifier(
            n_estimators=estimators, max_depth=depth, random_state=seed, n_jobs=-1
        )

    search_predictions = {}
    protected_predictions = {}
    final_predictions = {}
    start = time.perf_counter()
    for name, model in models.items():
        model.fit(x_fit, y_fit)
        search_predictions[name] = aligned_probability(model, x_search)
        protected_predictions[name] = aligned_probability(model, x_protected)
        final_predictions[name] = aligned_probability(model, x_final)
    fit_seconds = time.perf_counter() - start

    actions = np.eye(10)
    initial = np.ones(10) / 10
    audit_start = time.perf_counter()
    audit = audit_decision_model_selection(
        search_predictions,
        one_hot(y_search),
        protected_predictions,
        one_hot(y_protected),
        actions,
        initial_action_exposure=initial,
        transaction_cost=0.0,
        bootstrap_samples=500,
        random_seed=seed,
        material_regret=.002,
    )
    audit_seconds = time.perf_counter() - audit_start

    names, final_losses = decision_regret_matrix(
        final_predictions, one_hot(y_final), actions, initial_action_exposure=initial
    )
    selected = audit.decision_loss.selected_by_training_decision_loss
    rmse_selected = audit.decision_loss.selected_by_training_prediction_rmse
    protected_best = audit.protected_best_candidate
    final_rates = {
        "search_rmse_selected": float(final_losses[:, names.index(rmse_selected)].mean()),
        "search_decision_selected": float(final_losses[:, names.index(selected)].mean()),
        "protected_best": float(final_losses[:, names.index(protected_best)].mean()),
    }
    base = final_rates["search_decision_selected"]
    corrected = final_rates["protected_best"]
    return {
        "dataset": "scikit-learn load_digits / Optical Recognition of Handwritten Digits",
        "seed": seed,
        "split_rows": {
            "model_fit": len(y_fit), "search_selection": len(y_search),
            "protected_validation": len(y_protected), "fresh_final": len(y_final),
        },
        "candidate_models": len(models),
        "search_rmse_selected": rmse_selected,
        "search_decision_selected": selected,
        "protected_best_candidate": protected_best,
        "protected_audit_status": audit.adaptive_selection.status,
        "protected_selection_regret": audit.adaptive_selection.selected_holdout_regret,
        "selection_bootstrap_fragility": audit.adaptive_selection.selection_fragility,
        "fresh_final_error_rates": final_rates,
        "fresh_final_error_counts": {k: int(round(v * len(y_final))) for k, v in final_rates.items()},
        "fresh_final_relative_regret_reduction": 0.0 if base == 0 else 1.0 - corrected / base,
        "fit_seconds": fit_seconds,
        "audit_seconds": audit_seconds,
        "interpretation": "single fixed-seed real-data pilot; not a general-performance claim",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
