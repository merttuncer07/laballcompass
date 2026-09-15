"""Restart Timing Optimizer (RTO)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RestartPolicy:
    threshold: float | None
    expected_completion_time: float
    success_probability_per_attempt: float
    expected_failed_attempts: float
    expected_restart_overhead: float
    improvement_vs_no_restart: float


def evaluate_restart_threshold(
    completion_times: np.ndarray,
    threshold: float | None,
    restart_overhead: float = 0.0,
) -> RestartPolicy:
    samples = np.asarray(completion_times, dtype=float)
    if samples.ndim != 1 or samples.size == 0 or np.any(samples <= 0):
        raise ValueError("completion times must be a nonempty positive vector")
    if restart_overhead < 0:
        raise ValueError("restart overhead cannot be negative")
    no_restart = float(np.mean(samples))
    if threshold is None or np.isinf(threshold):
        return RestartPolicy(None, no_restart, 1.0, 0.0, 0.0, 0.0)
    tau = float(threshold)
    if tau <= 0:
        raise ValueError("restart threshold must be positive")
    success_probability = float(np.mean(samples <= tau))
    if success_probability <= 0:
        return RestartPolicy(tau, float("inf"), 0.0, float("inf"), float("inf"), float("-inf"))
    expected_failed = (1.0 - success_probability) / success_probability
    expected_overhead = restart_overhead * expected_failed
    expected_time = float(np.mean(np.minimum(samples, tau)) / success_probability + expected_overhead)
    improvement = 1.0 - expected_time / no_restart
    return RestartPolicy(
        tau,
        expected_time,
        success_probability,
        expected_failed,
        expected_overhead,
        improvement,
    )


def optimize_restart_threshold(
    completion_times: np.ndarray,
    restart_overhead: float = 0.0,
    candidate_thresholds: np.ndarray | None = None,
) -> RestartPolicy:
    samples = np.asarray(completion_times, dtype=float)
    if candidate_thresholds is None:
        quantiles = np.linspace(0.01, 0.99, 199)
        candidates = np.unique(np.quantile(samples, quantiles))
    else:
        candidates = np.unique(np.asarray(candidate_thresholds, dtype=float))
    policies = [evaluate_restart_threshold(samples, None, restart_overhead)]
    policies.extend(evaluate_restart_threshold(samples, value, restart_overhead) for value in candidates if value > 0)
    return min(policies, key=lambda policy: policy.expected_completion_time)

