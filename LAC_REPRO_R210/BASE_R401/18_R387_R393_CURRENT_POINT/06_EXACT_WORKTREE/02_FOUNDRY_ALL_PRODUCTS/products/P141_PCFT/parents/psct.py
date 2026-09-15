"""Predictive-State Discovery and Closure Tester (PSCT) v0.1."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from math import log
from typing import Hashable, Sequence

import numpy as np


@dataclass(frozen=True)
class PredictiveState:
    state_id: int
    contexts: tuple[tuple[Hashable, ...], ...]
    occurrence_count: int
    next_symbol_probabilities: tuple[float, ...]
    maximum_within_state_probability_distance: float


@dataclass(frozen=True)
class ClosureTransition:
    source_state: int
    observed_symbol: Hashable
    target_states: tuple[int, ...]
    occurrence_count: int
    majority_target_fraction: float
    closure_violation: bool


@dataclass(frozen=True)
class PredictiveStateResult:
    states: tuple[PredictiveState, ...]
    closure_transitions: tuple[ClosureTransition, ...]
    context_to_state: tuple[tuple[tuple[Hashable, ...], int], ...]
    alphabet: tuple[Hashable, ...]
    history_length: int
    observed_context_count: int
    predictive_state_count: int
    compression_fraction: float
    empirical_log_loss: float
    memoryless_log_loss: float
    predictive_log_loss_improvement: float
    closure_violation_rate: float
    unresolved_update_rate: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def discover_predictive_states(
    sequence: Sequence[Hashable],
    *,
    history_length: int,
    probability_tolerance: float,
    smoothing: float = 0.5,
) -> PredictiveStateResult:
    """Merge histories with similar next-observation laws and test update closure.

    Closure is evaluated separately: after appending the same observed symbol,
    all contexts in one discovered state should update to one target state. A
    good immediate forecast partition can therefore fail the state test.
    """

    values = tuple(sequence)
    if history_length < 1 or len(values) < 5 * history_length + 10:
        raise ValueError("sequence is too short for the requested history length")
    if probability_tolerance < 0 or probability_tolerance > 1 or smoothing < 0:
        raise ValueError("probability_tolerance must be in [0,1] and smoothing nonnegative")
    try:
        alphabet = tuple(sorted(set(values)))
    except TypeError:
        alphabet = tuple(dict.fromkeys(values))
    if len(alphabet) < 2:
        raise ValueError("at least two observable symbols are required")
    symbol_index = {symbol: index for index, symbol in enumerate(alphabet)}

    transition_counts: dict[tuple[Hashable, ...], np.ndarray] = {}
    context_counts: Counter = Counter()
    events: list[tuple[tuple[Hashable, ...], Hashable]] = []
    for position in range(history_length, len(values)):
        context = tuple(values[position - history_length:position])
        symbol = values[position]
        if context not in transition_counts:
            transition_counts[context] = np.zeros(len(alphabet), dtype=float)
        transition_counts[context][symbol_index[symbol]] += 1
        context_counts[context] += 1
        events.append((context, symbol))
    contexts = sorted(transition_counts, key=lambda item: tuple(map(str, item)))
    probabilities = {
        context: (transition_counts[context] + smoothing) /
        (context_counts[context] + smoothing * len(alphabet))
        for context in contexts
    }

    # Deterministic complete-link clustering: every pair in a state must satisfy
    # the declared predictive-distribution tolerance.
    clusters: list[list[tuple[Hashable, ...]]] = []
    for context in contexts:
        candidates = []
        for index, cluster in enumerate(clusters):
            distance = max(float(np.max(np.abs(probabilities[context] - probabilities[member]))) for member in cluster)
            if distance <= probability_tolerance + 1e-12:
                candidates.append((distance, -sum(context_counts[m] for m in cluster), index))
        if candidates:
            clusters[min(candidates)[2]].append(context)
        else:
            clusters.append([context])

    context_to_state: dict[tuple[Hashable, ...], int] = {}
    state_records: list[PredictiveState] = []
    for state_id, cluster in enumerate(clusters):
        counts = np.sum([transition_counts[context] for context in cluster], axis=0)
        total = sum(context_counts[context] for context in cluster)
        distribution = (counts + smoothing) / (total + smoothing * len(alphabet))
        maximum_distance = max(
            (float(np.max(np.abs(probabilities[left] - probabilities[right])))
             for i, left in enumerate(cluster) for right in cluster[i + 1:]),
            default=0.0,
        )
        for context in cluster:
            context_to_state[context] = state_id
        state_records.append(PredictiveState(
            state_id=state_id,
            contexts=tuple(cluster),
            occurrence_count=total,
            next_symbol_probabilities=tuple(map(float, distribution)),
            maximum_within_state_probability_distance=maximum_distance,
        ))

    update_counts: dict[tuple[int, Hashable], Counter] = defaultdict(Counter)
    unresolved = 0
    for context, symbol in events:
        source = context_to_state[context]
        updated = tuple((context + (symbol,))[-history_length:])
        if updated in context_to_state:
            update_counts[(source, symbol)][context_to_state[updated]] += 1
        else:
            unresolved += 1
    closure_records: list[ClosureTransition] = []
    violation_occurrences = 0
    resolved_occurrences = 0
    for (source, symbol), targets in sorted(update_counts.items(), key=lambda item: (item[0][0], str(item[0][1]))):
        count = sum(targets.values())
        majority = max(targets.values())
        violation = len(targets) > 1
        violation_occurrences += count - majority
        resolved_occurrences += count
        closure_records.append(ClosureTransition(
            source_state=source,
            observed_symbol=symbol,
            target_states=tuple(sorted(targets)),
            occurrence_count=count,
            majority_target_fraction=float(majority / count),
            closure_violation=violation,
        ))

    state_distributions = [np.asarray(state.next_symbol_probabilities) for state in state_records]
    global_counts = np.sum(list(transition_counts.values()), axis=0) + smoothing
    global_distribution = global_counts / global_counts.sum()
    empirical_loss = 0.0
    memoryless_loss = 0.0
    for context, symbol in events:
        index = symbol_index[symbol]
        empirical_loss -= log(max(1e-15, state_distributions[context_to_state[context]][index]))
        memoryless_loss -= log(max(1e-15, global_distribution[index]))
    empirical_loss /= len(events)
    memoryless_loss /= len(events)
    closure_rate = float(violation_occurrences / resolved_occurrences) if resolved_occurrences else 0.0
    unresolved_rate = float(unresolved / len(events))
    if unresolved_rate > 0:
        status = "PREDICTIVE_STATES_HAVE_UNRESOLVED_UPDATES"
    elif closure_rate > 0:
        status = "PREDICTIVE_PARTITION_FAILS_CLOSURE"
    else:
        status = "PREDICTIVE_STATE_CLOSURE_CERTIFIED_ON_OBSERVED_CONTEXTS"
    return PredictiveStateResult(
        states=tuple(state_records),
        closure_transitions=tuple(closure_records),
        context_to_state=tuple((context, context_to_state[context]) for context in contexts),
        alphabet=alphabet,
        history_length=history_length,
        observed_context_count=len(contexts),
        predictive_state_count=len(clusters),
        compression_fraction=float(1.0 - len(clusters) / len(contexts)),
        empirical_log_loss=float(empirical_loss),
        memoryless_log_loss=float(memoryless_loss),
        predictive_log_loss_improvement=float(memoryless_loss - empirical_loss),
        closure_violation_rate=closure_rate,
        unresolved_update_rate=unresolved_rate,
        status=status,
    )
