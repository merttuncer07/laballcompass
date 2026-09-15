"""Train and validate a restart threshold on broad completion times."""

from __future__ import annotations

import json

import numpy as np

from rto import evaluate_restart_threshold, optimize_restart_threshold


def serializable(policy):
    return policy.__dict__


def main() -> None:
    training_rng = np.random.default_rng(430031)
    validation_rng = np.random.default_rng(430032)
    training = training_rng.lognormal(mean=2.0, sigma=1.45, size=120_000)
    validation = validation_rng.lognormal(mean=2.0, sigma=1.45, size=120_000)
    overhead = 1.0
    trained = optimize_restart_threshold(training, overhead)
    validation_policy = evaluate_restart_threshold(validation, trained.threshold, overhead)
    no_restart = evaluate_restart_threshold(validation, None, overhead)
    median_rule = evaluate_restart_threshold(validation, float(np.median(training)), overhead)
    output = {
        "training_samples": int(training.size),
        "validation_samples": int(validation.size),
        "restart_overhead": overhead,
        "trained_policy": serializable(trained),
        "validation_policy": serializable(validation_policy),
        "validation_no_restart": serializable(no_restart),
        "validation_median_restart": serializable(median_rule),
        "validated_time_reduction": 1.0
        - validation_policy.expected_completion_time / no_restart.expected_completion_time,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

