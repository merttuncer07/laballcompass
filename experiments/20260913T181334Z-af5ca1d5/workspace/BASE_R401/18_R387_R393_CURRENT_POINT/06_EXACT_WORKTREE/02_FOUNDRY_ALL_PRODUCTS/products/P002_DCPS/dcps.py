"""Decision-Closed Predictive State (DCPS) v0.1.

PSCT -> DSBC composition with an explicit post-compression closure refinement, plus adapters to CAPL
and DLEW.  Decision-safe merging is allowed only as far as recursively usable predictive dynamics
remain certified on the observed training contexts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Hashable, Mapping, Sequence

import numpy as np

if __package__:
    from .parents.capl import PortfolioPolicyResult, learn_portfolio_policy
else:
    from parents.capl import PortfolioPolicyResult, learn_portfolio_policy
if __package__:
    from .parents.dlew import DecisionLossWorkbenchResult, evaluate_decision_models
else:
    from parents.dlew import DecisionLossWorkbenchResult, evaluate_decision_models
if __package__:
    from .parents.dsbc import BeliefCompressionResult, compress_beliefs
else:
    from parents.dsbc import BeliefCompressionResult, compress_beliefs
if __package__:
    from .parents.psct import PredictiveStateResult, discover_predictive_states
else:
    from parents.psct import PredictiveStateResult, discover_predictive_states


@dataclass(frozen=True)
class DecisionClosedCluster:
    cluster_id: int
    predictive_state_ids: tuple[int, ...]
    representative_predictive_belief: tuple[float, ...]
    prescribed_action: int
    maximum_decision_regret: float
    mean_decision_regret: float
    action_margin: float
    observed_transition_targets: tuple[tuple[Hashable, int | None], ...]


@dataclass(frozen=True)
class DecisionClosedRepresentation:
    predictive_state_result: PredictiveStateResult
    initial_decision_compression: BeliefCompressionResult
    clusters: tuple[DecisionClosedCluster, ...]
    predictive_state_to_cluster: tuple[int, ...]
    initial_decision_cluster_count: int
    decision_closed_cluster_count: int
    closure_refinement_splits: int
    predictive_state_compression_fraction: float
    context_compression_fraction: float
    maximum_decision_regret: float
    closure_certified: bool
    unresolved_transition_fraction: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SequenceFeatureMatrix:
    row_indices: tuple[int, ...]
    features: tuple[tuple[float, ...], ...]
    cluster_ids: tuple[int, ...]
    unresolved_row_indices: tuple[int, ...]

    def as_array(self) -> np.ndarray:
        return np.asarray(self.features, dtype=float)


@dataclass(frozen=True)
class RepresentationDLEWResult:
    decision_loss: DecisionLossWorkbenchResult
    candidate_names: tuple[str, ...]
    fit_fallback_counts: tuple[tuple[str, int], ...]
    selection_fallback_counts: tuple[tuple[str, int], ...]
    validation_fallback_counts: tuple[tuple[str, int], ...]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _state_beliefs(psct: PredictiveStateResult) -> tuple[np.ndarray, np.ndarray]:
    ordered = sorted(psct.states, key=lambda state: state.state_id)
    if [state.state_id for state in ordered] != list(range(len(ordered))):
        raise ValueError("PSCT state ids must be contiguous from zero")
    beliefs = np.asarray([state.next_symbol_probabilities for state in ordered], dtype=float)
    weights = np.asarray([state.occurrence_count for state in ordered], dtype=float)
    return beliefs, weights


def _transition_table(psct: PredictiveStateResult) -> dict[tuple[int, Hashable], int]:
    table: dict[tuple[int, Hashable], int] = {}
    for transition in psct.closure_transitions:
        if len(transition.target_states) == 1:
            table[(transition.source_state, transition.observed_symbol)] = transition.target_states[0]
    return table


def _partition_from_assignments(assignments: Sequence[int]) -> list[tuple[int, ...]]:
    groups: dict[int, list[int]] = {}
    for state_id, cluster_id in enumerate(assignments):
        groups.setdefault(int(cluster_id), []).append(state_id)
    return [tuple(groups[key]) for key in sorted(groups, key=lambda k: min(groups[k]))]


def _assignment_from_partition(partition: Sequence[Sequence[int]], states: int) -> np.ndarray:
    assignment = np.empty(states, dtype=int)
    for cluster_id, members in enumerate(partition):
        for state_id in members:
            assignment[int(state_id)] = cluster_id
    return assignment


def _refine_for_closure(
    partition: list[tuple[int, ...]],
    psct: PredictiveStateResult,
) -> tuple[list[tuple[int, ...]], int]:
    """Split only; never merge. Repeatedly refine by aggregate transition signatures."""
    table = _transition_table(psct)
    alphabet = psct.alphabet
    splits = 0
    while True:
        assignment = _assignment_from_partition(partition, len(psct.states))
        changed = False
        refined: list[tuple[int, ...]] = []
        for members in partition:
            buckets: dict[tuple[int | None, ...], list[int]] = {}
            for source in members:
                signature = []
                for symbol in alphabet:
                    target = table.get((source, symbol))
                    signature.append(None if target is None else int(assignment[target]))
                buckets.setdefault(tuple(signature), []).append(source)
            if len(buckets) > 1:
                changed = True
                splits += len(buckets) - 1
            refined.extend(tuple(bucket) for _, bucket in sorted(buckets.items(), key=lambda item: min(item[1])))
        refined.sort(key=lambda members: min(members))
        partition = refined
        if not changed:
            return partition, splits


def _cluster_metrics(
    members: Sequence[int],
    beliefs: np.ndarray,
    utilities: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, int, float, float, float]:
    idx = np.asarray(members, dtype=int)
    values = beliefs[idx] @ utilities
    optimal = np.max(values, axis=1)
    regrets = optimal[:, None] - values
    local_weights = weights[idx]
    action_max = np.max(regrets, axis=0)
    action_mean = np.average(regrets, axis=0, weights=local_weights)
    action = int(min(range(utilities.shape[1]), key=lambda j: (action_max[j], action_mean[j], j)))
    representative = np.average(beliefs[idx], axis=0, weights=local_weights)
    rep_values = representative @ utilities
    ordered = np.sort(rep_values)
    margin = float(ordered[-1] - ordered[-2])
    return representative, action, float(action_max[action]), float(action_mean[action]), margin


def build_decision_closed_representation(
    sequence: Sequence[Hashable],
    state_action_utilities: Sequence[Sequence[float]],
    *,
    history_length: int,
    probability_tolerance: float,
    maximum_decision_regret: float,
    smoothing: float = 0.5,
) -> DecisionClosedRepresentation:
    """Discover observable predictive states, compress by decision loss, then restore closure by splitting.

    Rows of ``state_action_utilities`` correspond to PSCT's observable alphabet in exactly the order
    reported by PSCT; columns are downstream discrete actions.
    """
    psct = discover_predictive_states(
        sequence,
        history_length=history_length,
        probability_tolerance=probability_tolerance,
        smoothing=smoothing,
    )
    beliefs, weights = _state_beliefs(psct)
    utilities = np.asarray(state_action_utilities, dtype=float)
    if utilities.ndim != 2 or utilities.shape[0] != len(psct.alphabet) or utilities.shape[1] < 2:
        raise ValueError("state_action_utilities rows must match the PSCT alphabet and have >=2 actions")
    dsbc = compress_beliefs(
        beliefs,
        utilities,
        maximum_regret=maximum_decision_regret,
        sample_weights=weights,
    )
    initial_partition = _partition_from_assignments(dsbc.assignments)
    parent_closed = psct.closure_violation_rate <= 1e-15 and psct.unresolved_update_rate <= 1e-15
    if parent_closed:
        partition, splits = _refine_for_closure(initial_partition, psct)
    else:
        partition, splits = initial_partition, 0
    assignment = _assignment_from_partition(partition, len(psct.states))
    table = _transition_table(psct)
    records = []
    global_max = 0.0
    for cluster_id, members in enumerate(partition):
        representative, action, max_regret, mean_regret, margin = _cluster_metrics(
            members, beliefs, utilities, weights
        )
        global_max = max(global_max, max_regret)
        transitions = []
        for symbol in psct.alphabet:
            targets = {
                int(assignment[target])
                for state in members
                if (target := table.get((state, symbol))) is not None
            }
            target = next(iter(targets)) if len(targets) == 1 else None
            transitions.append((symbol, target))
        records.append(DecisionClosedCluster(
            cluster_id=cluster_id,
            predictive_state_ids=tuple(members),
            representative_predictive_belief=tuple(map(float, representative)),
            prescribed_action=action,
            maximum_decision_regret=max_regret,
            mean_decision_regret=mean_regret,
            action_margin=margin,
            observed_transition_targets=tuple(transitions),
        ))
    closure_certified = parent_closed
    if closure_certified:
        # Postcondition: every observed source-cluster/symbol combination has <=1 target cluster.
        for cluster in records:
            for symbol, target in cluster.observed_transition_targets:
                source_targets = {
                    int(assignment[t])
                    for state in cluster.predictive_state_ids
                    if (t := table.get((state, symbol))) is not None
                }
                if len(source_targets) > 1 or (source_targets and target is None):
                    closure_certified = False
    if not parent_closed:
        status = "PARENT_PREDICTIVE_PARTITION_NOT_CLOSED"
    elif splits:
        status = "DECISION_COMPRESSION_REFINED_TO_RESTORE_CLOSURE"
    else:
        status = "DECISION_COMPRESSION_PRESERVES_PREDICTIVE_CLOSURE"
    return DecisionClosedRepresentation(
        predictive_state_result=psct,
        initial_decision_compression=dsbc,
        clusters=tuple(records),
        predictive_state_to_cluster=tuple(map(int, assignment)),
        initial_decision_cluster_count=len(initial_partition),
        decision_closed_cluster_count=len(partition),
        closure_refinement_splits=splits,
        predictive_state_compression_fraction=float(1.0 - len(partition) / len(psct.states)),
        context_compression_fraction=float(1.0 - len(partition) / psct.observed_context_count),
        maximum_decision_regret=float(global_max),
        closure_certified=closure_certified,
        unresolved_transition_fraction=float(psct.unresolved_update_rate),
        status=status,
    )


def transform_sequence(
    representation: DecisionClosedRepresentation,
    sequence: Sequence[Hashable],
) -> SequenceFeatureMatrix:
    """Map causal history contexts to one-hot decision-closed state features."""
    values = tuple(sequence)
    h = representation.predictive_state_result.history_length
    context_to_state = dict(representation.predictive_state_result.context_to_state)
    state_to_cluster = representation.predictive_state_to_cluster
    k = representation.decision_closed_cluster_count
    rows: list[int] = []
    clusters: list[int] = []
    unresolved: list[int] = []
    feature_rows: list[tuple[float, ...]] = []
    for position in range(h, len(values)):
        context = tuple(values[position - h:position])
        state = context_to_state.get(context)
        if state is None:
            unresolved.append(position)
            continue
        cluster = state_to_cluster[state]
        vector = np.zeros(k, dtype=float)
        vector[cluster] = 1.0
        rows.append(position)
        clusters.append(cluster)
        feature_rows.append(tuple(map(float, vector)))
    return SequenceFeatureMatrix(
        row_indices=tuple(rows),
        features=tuple(feature_rows),
        cluster_ids=tuple(clusters),
        unresolved_row_indices=tuple(unresolved),
    )


def learn_constrained_policy_from_representation(
    representation: DecisionClosedRepresentation,
    training_sequence: Sequence[Hashable],
    training_asset_returns: Sequence[Sequence[float]],
    validation_sequence: Sequence[Hashable],
    validation_asset_returns: Sequence[Sequence[float]],
    *,
    require_complete_context_coverage: bool = True,
    **capl_kwargs: Any,
) -> PortfolioPolicyResult:
    """DSBC/closure representation -> CAPL one-hot features, aligned causally to contemporaneous returns."""
    train_returns = np.asarray(training_asset_returns, dtype=float)
    val_returns = np.asarray(validation_asset_returns, dtype=float)
    if train_returns.ndim != 2 or val_returns.ndim != 2:
        raise ValueError("asset returns must be matrices")
    if train_returns.shape[0] != len(training_sequence) or val_returns.shape[0] != len(validation_sequence):
        raise ValueError("each sequence must have one aligned asset-return row per symbol")
    train_features = transform_sequence(representation, training_sequence)
    val_features = transform_sequence(representation, validation_sequence)
    if require_complete_context_coverage and (train_features.unresolved_row_indices or val_features.unresolved_row_indices):
        raise ValueError("unseen contexts found; protected transformation will not silently impute a state")
    train_rows = np.asarray(train_features.row_indices, dtype=int)
    val_rows = np.asarray(val_features.row_indices, dtype=int)
    return learn_portfolio_policy(
        train_features.as_array(),
        train_returns[train_rows],
        val_features.as_array(),
        val_returns[val_rows],
        **capl_kwargs,
    )


def _keys_for_level(
    representation: DecisionClosedRepresentation,
    sequence: Sequence[Hashable],
    level: str,
) -> tuple[list[Any], list[int]]:
    psct = representation.predictive_state_result
    values = tuple(sequence)
    context_to_state = dict(psct.context_to_state)
    keys = []
    rows = []
    for position in range(psct.history_length, len(values)):
        context = tuple(values[position - psct.history_length:position])
        state = context_to_state.get(context)
        if state is None:
            continue
        if level == "raw_context": key = context
        elif level == "predictive_state": key = state
        elif level == "decision_closed": key = representation.predictive_state_to_cluster[state]
        else: raise ValueError(f"unknown level {level}")
        keys.append(key); rows.append(position)
    return keys, rows


def evaluate_representation_predictors(
    representation: DecisionClosedRepresentation,
    fit_sequence: Sequence[Hashable],
    fit_asset_returns: Sequence[Sequence[float]],
    selection_sequence: Sequence[Hashable],
    selection_asset_returns: Sequence[Sequence[float]],
    validation_sequence: Sequence[Hashable],
    validation_asset_returns: Sequence[Sequence[float]],
    action_payoff_exposures: Sequence[Sequence[float]],
    *,
    initial_action_exposure: Sequence[float],
    transaction_cost: float = 0.0,
) -> RepresentationDLEWResult:
    """Fit mean-return predictors at several representation resolutions and compare them with DLEW."""
    fit_r = np.asarray(fit_asset_returns, dtype=float)
    sel_r = np.asarray(selection_asset_returns, dtype=float)
    val_r = np.asarray(validation_asset_returns, dtype=float)
    if fit_r.ndim != 2 or sel_r.ndim != 2 or val_r.ndim != 2:
        raise ValueError("asset returns must be matrices")
    if fit_r.shape[0] != len(fit_sequence) or sel_r.shape[0] != len(selection_sequence) or val_r.shape[0] != len(validation_sequence):
        raise ValueError("sequence/return row alignment mismatch")
    if fit_r.shape[1] != sel_r.shape[1] or fit_r.shape[1] != val_r.shape[1]:
        raise ValueError("asset dimensions must match")
    h = representation.predictive_state_result.history_length
    candidate_levels = ("memoryless", "raw_context", "predictive_state", "decision_closed")
    predictions_selection: dict[str, np.ndarray] = {}
    predictions_validation: dict[str, np.ndarray] = {}
    fit_fallback = []; selection_fallback = []; validation_fallback = []
    global_mean = fit_r[h:].mean(axis=0)

    # All candidates are evaluated on rows h: to keep outcome matrices identical.
    selection_outcomes = sel_r[h:]
    validation_outcomes = val_r[h:]
    for level in candidate_levels:
        if level == "memoryless":
            predictions_selection[level] = np.tile(global_mean, (len(selection_outcomes), 1))
            predictions_validation[level] = np.tile(global_mean, (len(validation_outcomes), 1))
            fit_fallback.append((level, 0)); selection_fallback.append((level, 0)); validation_fallback.append((level, 0))
            continue
        fit_keys, fit_rows = _keys_for_level(representation, fit_sequence, level)
        means: dict[Any, np.ndarray] = {}
        for key in dict.fromkeys(fit_keys):
            rows = [row for k, row in zip(fit_keys, fit_rows) if k == key]
            means[key] = fit_r[np.asarray(rows, dtype=int)].mean(axis=0)
        def predict(seq, expected_rows):
            keys, rows = _keys_for_level(representation, seq, level)
            by_position = {row: key for key, row in zip(keys, rows)}
            output = np.empty((expected_rows, fit_r.shape[1]), dtype=float)
            fallback = 0
            for offset, position in enumerate(range(h, h + expected_rows)):
                key = by_position.get(position)
                if key is None or key not in means:
                    output[offset] = global_mean; fallback += 1
                else:
                    output[offset] = means[key]
            return output, fallback
        sel_pred, sel_fb = predict(selection_sequence, len(selection_outcomes))
        val_pred, val_fb = predict(validation_sequence, len(validation_outcomes))
        predictions_selection[level] = sel_pred
        predictions_validation[level] = val_pred
        fit_fallback.append((level, 0)); selection_fallback.append((level, sel_fb)); validation_fallback.append((level, val_fb))

    dlew = evaluate_decision_models(
        predictions_selection,
        selection_outcomes,
        predictions_validation,
        validation_outcomes,
        action_payoff_exposures,
        initial_action_exposure=initial_action_exposure,
        transaction_cost=transaction_cost,
    )
    fallbacks = sum(v for _, v in selection_fallback + validation_fallback)
    return RepresentationDLEWResult(
        decision_loss=dlew,
        candidate_names=candidate_levels,
        fit_fallback_counts=tuple(fit_fallback),
        selection_fallback_counts=tuple(selection_fallback),
        validation_fallback_counts=tuple(validation_fallback),
        status="REPRESENTATION_PREDICTORS_EVALUATED_WITH_FALLBACKS" if fallbacks else "REPRESENTATION_PREDICTORS_EVALUATED_WITHOUT_FALLBACKS",
    )
