"""State Aggregation and Lumpability Certificate (SALC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class LumpabilityCertificate:
    micro_states: int
    aggregate_states: int
    block_labels: tuple[str, ...]
    exact_lumpability: bool
    maximum_block_transition_deviation: float
    maximum_one_step_total_variation: float
    maximum_horizon_total_variation: float
    horizon: int
    worst_source_block: str
    worst_target_block: str
    worst_state_pair: tuple[int, int]
    aggregate_transition_matrix: tuple[tuple[float, ...], ...]
    block_transition_signatures: tuple[tuple[float, ...], ...]
    compression_ratio: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def audit_lumpability(
    transition_matrix: Sequence[Sequence[float]],
    partition: Sequence[str],
    *,
    tolerance: float = 1e-10,
    horizon: int = 20,
    allowed_horizon_tv: float | None = None,
) -> LumpabilityCertificate:
    """Certify exact or quantified approximate strong lumpability of a finite Markov chain."""

    p = np.asarray(transition_matrix, dtype=float)
    if p.ndim != 2 or p.shape[0] != p.shape[1] or p.shape[0] == 0:
        raise ValueError("transition_matrix must be non-empty and square")
    n = p.shape[0]
    if len(partition) != n or any(not str(label) for label in partition):
        raise ValueError("partition must provide one non-empty block label per state")
    if not np.all(np.isfinite(p)) or np.any(p < -tolerance) or not np.allclose(np.sum(p, axis=1), 1.0, atol=tolerance):
        raise ValueError("transition matrix must be finite, non-negative, and row stochastic")
    if tolerance < 0 or not isinstance(horizon, int) or horizon < 1:
        raise ValueError("tolerance must be non-negative and horizon a positive integer")
    if allowed_horizon_tv is not None and not 0 <= allowed_horizon_tv <= 1:
        raise ValueError("allowed_horizon_tv must lie in [0,1]")
    p = np.maximum(p, 0); p /= np.sum(p, axis=1, keepdims=True)

    labels = tuple(dict.fromkeys(map(str, partition)))
    indices = {label: np.where(np.asarray(partition, dtype=str) == label)[0] for label in labels}
    signatures = np.column_stack([np.sum(p[:, states], axis=1) for states in indices.values()])
    aggregate = np.vstack([np.mean(signatures[states], axis=0) for states in indices.values()])

    max_deviation = -1.0; worst_source = labels[0]; worst_target = labels[0]; worst_pair = (0, 0)
    for source_label, states in indices.items():
        for target_index, target_label in enumerate(labels):
            column = signatures[states, target_index]
            deviation = float(np.max(column) - np.min(column))
            if deviation > max_deviation:
                max_deviation = deviation; worst_source = source_label; worst_target = target_label
                worst_pair = (int(states[np.argmin(column)]), int(states[np.argmax(column)]))
    row_means = np.vstack([aggregate[labels.index(str(label))] for label in partition])
    one_step_tv = float(np.max(0.5 * np.sum(np.abs(signatures - row_means), axis=1)))

    original_power = np.eye(n); aggregate_power = np.eye(len(labels)); maximum_horizon_tv = 0.0
    membership = np.zeros((n, len(labels)))
    for block_index, label in enumerate(labels): membership[indices[label], block_index] = 1.0
    for _ in range(1, horizon + 1):
        original_power = original_power @ p; aggregate_power = aggregate_power @ aggregate
        original_blocks = original_power @ membership
        predicted = np.vstack([aggregate_power[labels.index(str(label))] for label in partition])
        maximum_horizon_tv = max(
            maximum_horizon_tv, float(np.max(0.5 * np.sum(np.abs(original_blocks - predicted), axis=1)))
        )

    exact = max_deviation <= tolerance
    if exact:
        status = "EXACT_LUMPABILITY_CERTIFIED"
    elif allowed_horizon_tv is None or maximum_horizon_tv <= allowed_horizon_tv:
        status = "APPROXIMATE_WITH_QUANTIFIED_ERROR"
    else:
        status = "DECLARED_ERROR_BUDGET_EXCEEDED"
    return LumpabilityCertificate(
        n, len(labels), labels, exact, max_deviation, one_step_tv, maximum_horizon_tv, horizon,
        worst_source, worst_target, worst_pair, tuple(tuple(map(float, row)) for row in aggregate),
        tuple(tuple(map(float, row)) for row in signatures), float(len(labels) / n), status,
    )
