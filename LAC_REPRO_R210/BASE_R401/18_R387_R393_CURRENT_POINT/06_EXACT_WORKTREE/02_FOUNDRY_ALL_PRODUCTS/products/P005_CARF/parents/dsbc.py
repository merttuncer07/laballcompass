"""Decision-Sufficient Belief Compressor (DSBC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class BeliefCluster:
    cluster_id: int
    member_indices: tuple[int, ...]
    representative_belief: tuple[float, ...]
    prescribed_action: int
    maximum_decision_regret: float
    mean_decision_regret: float
    action_margin_at_representative: float


@dataclass(frozen=True)
class BeliefCompressionResult:
    assignments: tuple[int, ...]
    clusters: tuple[BeliefCluster, ...]
    original_belief_count: int
    compressed_state_count: int
    compression_fraction: float
    global_maximum_regret: float
    global_weighted_mean_regret: float
    requested_regret_tolerance: float
    merge_certificate: str
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _cluster_choice(
    members: tuple[int, ...],
    beliefs: np.ndarray,
    utilities: np.ndarray,
    weights: np.ndarray,
) -> tuple[int, np.ndarray, np.ndarray, float, float]:
    values = beliefs[list(members)] @ utilities
    optimal = np.max(values, axis=1)
    action_regrets = optimal[:, None] - values
    local_weights = weights[list(members)]
    action_max = np.max(action_regrets, axis=0)
    action_mean = np.average(action_regrets, axis=0, weights=local_weights)
    action = int(min(range(utilities.shape[1]), key=lambda j: (action_max[j], action_mean[j], j)))
    representative = np.average(beliefs[list(members)], axis=0, weights=local_weights)
    return action, representative, action_regrets[:, action], float(action_max[action]), float(action_mean[action])


def compress_beliefs(
    beliefs: Sequence[Sequence[float]],
    state_action_utilities: Sequence[Sequence[float]],
    *,
    maximum_regret: float,
    sample_weights: Sequence[float] | None = None,
) -> BeliefCompressionResult:
    """Greedily merge posterior beliefs while certifying downstream decision regret.

    The utility matrix has one row per hidden state and one column per available
    action. A cluster is admissible only if one common action loses no more than
    ``maximum_regret`` for every belief assigned to it.
    """

    posterior = np.asarray(beliefs, dtype=float)
    utilities = np.asarray(state_action_utilities, dtype=float)
    if posterior.ndim != 2 or utilities.ndim != 2:
        raise ValueError("beliefs and utilities must be matrices")
    if posterior.shape[0] < 1 or posterior.shape[1] < 2 or utilities.shape[0] != posterior.shape[1] or utilities.shape[1] < 2:
        raise ValueError("belief and state/action dimensions do not match")
    if not np.all(np.isfinite(posterior)) or not np.all(np.isfinite(utilities)):
        raise ValueError("beliefs and utilities must be finite")
    if np.any(posterior < -1e-12) or not np.allclose(posterior.sum(axis=1), 1.0, atol=1e-8):
        raise ValueError("every belief must be a probability vector")
    if maximum_regret < 0 or not np.isfinite(maximum_regret):
        raise ValueError("maximum_regret must be finite and nonnegative")
    n = posterior.shape[0]
    weights = np.ones(n) if sample_weights is None else np.asarray(sample_weights, dtype=float)
    if weights.shape != (n,) or np.any(weights <= 0) or not np.all(np.isfinite(weights)):
        raise ValueError("sample_weights must be positive and match beliefs")

    tolerance = maximum_regret + 1e-12
    # Build clusters online first. This avoids repeatedly scoring every pair of
    # singleton clusters while still checking the hard regret condition on each
    # proposed addition.
    clusters: list[tuple[int, ...]] = []
    for index in range(n):
        candidates: list[tuple[tuple[float, float, int, int], int, tuple[int, ...]]] = []
        for cluster_index, cluster in enumerate(clusters):
            merged = tuple(sorted(cluster + (index,)))
            _, _, _, max_loss, mean_loss = _cluster_choice(merged, posterior, utilities, weights)
            if max_loss <= tolerance:
                candidates.append(((max_loss, mean_loss, -len(merged), cluster[0]), cluster_index, merged))
        if candidates:
            _, cluster_index, merged = min(candidates, key=lambda item: item[0])
            clusters[cluster_index] = merged
        else:
            clusters.append((index,))

    # A short agglomeration pass removes any order-induced merge opportunity and
    # supplies the reported local no-more-merges certificate.
    while True:
        feasible: list[tuple[tuple[float, float, int, int, int], int, int, tuple[int, ...]]] = []
        for left in range(len(clusters)):
            for right in range(left + 1, len(clusters)):
                merged = tuple(sorted(clusters[left] + clusters[right]))
                _, _, _, max_loss, mean_loss = _cluster_choice(merged, posterior, utilities, weights)
                if max_loss <= tolerance:
                    # Prefer tight certificates, then large useful merges and deterministic IDs.
                    score = (max_loss, mean_loss, -len(merged), merged[0], merged[-1])
                    feasible.append((score, left, right, merged))
        if not feasible:
            break
        _, left, right, merged = min(feasible, key=lambda item: item[0])
        clusters = [cluster for index, cluster in enumerate(clusters) if index not in (left, right)] + [merged]
        clusters.sort(key=lambda member: member[0])

    records: list[BeliefCluster] = []
    assignments = np.empty(n, dtype=int)
    all_regrets = np.empty(n, dtype=float)
    for cluster_id, members in enumerate(clusters):
        action, representative, regrets, max_loss, mean_loss = _cluster_choice(
            members, posterior, utilities, weights
        )
        representative_values = representative @ utilities
        ordered = np.sort(representative_values)
        margin = float(ordered[-1] - ordered[-2])
        for member, regret in zip(members, regrets):
            assignments[member] = cluster_id
            all_regrets[member] = regret
        records.append(BeliefCluster(
            cluster_id=cluster_id,
            member_indices=members,
            representative_belief=tuple(map(float, representative)),
            prescribed_action=action,
            maximum_decision_regret=max_loss,
            mean_decision_regret=mean_loss,
            action_margin_at_representative=margin,
        ))
    certificate = (
        "NO_REMAINING_PAIRWISE_MERGE_WITHIN_TOLERANCE"
        if len(clusters) > 1 else "ALL_BELIEFS_SHARE_ONE_TOLERANCE_SAFE_ACTION"
    )
    global_max = float(np.max(all_regrets))
    return BeliefCompressionResult(
        assignments=tuple(map(int, assignments)),
        clusters=tuple(records),
        original_belief_count=n,
        compressed_state_count=len(clusters),
        compression_fraction=float(1.0 - len(clusters) / n),
        global_maximum_regret=global_max,
        global_weighted_mean_regret=float(np.average(all_regrets, weights=weights)),
        requested_regret_tolerance=float(maximum_regret),
        merge_certificate=certificate,
        status="DECISION_SUFFICIENT_BELIEF_COMPRESSION_CERTIFIED",
    )
