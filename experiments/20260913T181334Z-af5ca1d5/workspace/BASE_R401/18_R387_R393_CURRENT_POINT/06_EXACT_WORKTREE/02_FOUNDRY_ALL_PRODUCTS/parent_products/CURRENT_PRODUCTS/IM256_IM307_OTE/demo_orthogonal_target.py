from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ote import OrthogonalTargetEstimator, estimate_from_nuisance_predictions


def evaluate() -> dict[str, object]:
    rng = np.random.default_rng(20260825)
    n = 20_000
    theta = 2.0
    representation = rng.normal(size=(n, 3))
    treatment_mean = representation @ np.array([1.2, -0.8, 0.6])
    treatment = treatment_mean + rng.normal(0.0, 1.0, n)
    outcome_mean_without_target = representation @ np.array([1.0, 0.7, -0.5])
    outcome = theta * treatment + outcome_mean_without_target + rng.normal(0.0, 1.0, n)

    naive = float((treatment @ outcome) / (treatment @ treatment))
    orthogonal = OrthogonalTargetEstimator(folds=5).fit(representation, treatment, outcome)

    true_outcome_prediction = theta * treatment_mean + outcome_mean_without_target
    direction_m = rng.normal(size=n)
    direction_l = rng.normal(size=n)
    perturbations = {}
    for delta in (0.0, 0.05, 0.10, 0.20):
        estimate = estimate_from_nuisance_predictions(
            treatment,
            outcome,
            treatment_mean + delta * direction_m,
            true_outcome_prediction + delta * direction_l,
        )
        perturbations[str(delta)] = estimate.target

    return {
        "true_target": theta,
        "naive_unadjusted_target": naive,
        "orthogonal_crossfit": orthogonal.as_dict(),
        "absolute_error_naive": abs(naive - theta),
        "absolute_error_orthogonal": abs(orthogonal.target - theta),
        "nuisance_perturbation_path": perturbations,
        "observations": n,
        "representation_dimensions": 3,
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("orthogonal_target_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
