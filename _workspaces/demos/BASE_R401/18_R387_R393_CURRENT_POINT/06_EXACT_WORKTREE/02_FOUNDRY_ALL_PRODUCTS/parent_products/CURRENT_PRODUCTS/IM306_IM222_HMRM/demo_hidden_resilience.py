"""Benchmark scalar-only, recovery-only, and joint hidden-mode monitoring."""

from __future__ import annotations

import json

import numpy as np

from hmrm import HiddenModeResilienceMonitor


def rates(predictions: list[bool], labels: list[bool]) -> dict[str, float]:
    tp = sum(pred and label for pred, label in zip(predictions, labels))
    fp = sum(pred and not label for pred, label in zip(predictions, labels))
    tn = sum(not pred and not label for pred, label in zip(predictions, labels))
    fn = sum(not pred and label for pred, label in zip(predictions, labels))
    return {
        "true_positive_rate": tp / max(tp + fn, 1),
        "false_positive_rate": fp / max(fp + tn, 1),
        "balanced_accuracy": 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)),
    }


def main() -> None:
    rng = np.random.default_rng(306222)
    monitor = HiddenModeResilienceMonitor(
        minimum_exposure=0.04,
        minimum_recovery_steps=30,
        recovery_floor=0.005,
        scalar_alarm_distance=0.08,
    )
    labels: list[bool] = []
    scalar_predictions: list[bool] = []
    recovery_predictions: list[bool] = []
    joint_predictions: list[bool] = []
    hidden_cancellation_examples = 0
    for group in ("dangerous_hidden", "inactive_slow", "fast_visible"):
        for _ in range(600):
            if group == "dangerous_hidden":
                slow = rng.uniform(0.965, 0.995)
                slow_amplitude = rng.uniform(0.06, 0.25)
                fast_amplitude = -slow_amplitude + rng.normal(0.0, 0.008)
                transition = np.diag([rng.uniform(0.35, 0.70), slow])
                state = np.array([fast_amplitude, slow_amplitude])
                label = True
            elif group == "inactive_slow":
                transition = np.diag([rng.uniform(0.35, 0.70), rng.uniform(0.965, 0.995)])
                state = np.array([rng.normal(0.0, 0.025), rng.uniform(0.0001, 0.004)])
                label = False
            else:
                transition = np.diag([rng.uniform(0.25, 0.55), rng.uniform(0.55, 0.78)])
                state = rng.normal(0.0, 0.07, size=2)
                label = False
            assessment = monitor.assess(transition, state, np.ones(2))
            labels.append(label)
            scalar_predictions.append(assessment.scalar_only_alert)
            recovery_predictions.append(assessment.recovery_only_alert)
            joint_predictions.append(assessment.joint_alert)
            hidden_cancellation_examples += int(label and assessment.observed_scalar_distance < 0.02)
    result = {
        "cases": len(labels),
        "dangerous_cases_hidden_by_scalar_cancellation": hidden_cancellation_examples,
        "scalar_only": rates(scalar_predictions, labels),
        "recovery_time_only": rates(recovery_predictions, labels),
        "joint_exposure_recovery": rates(joint_predictions, labels),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

