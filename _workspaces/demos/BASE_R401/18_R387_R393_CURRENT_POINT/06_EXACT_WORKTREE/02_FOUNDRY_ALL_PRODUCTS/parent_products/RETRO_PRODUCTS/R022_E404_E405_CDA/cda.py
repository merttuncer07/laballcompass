"""Channel Dominance Auditor (CDA)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class GarblingCertificate:
    source_dominates_target: bool
    garbling_matrix: np.ndarray
    maximum_reconstruction_error: float


@dataclass(frozen=True)
class ChannelAudit:
    relation: str
    first_to_second: GarblingCertificate
    second_to_first: GarblingCertificate


def _validate_channel(channel: np.ndarray) -> np.ndarray:
    matrix = np.asarray(channel, dtype=float)
    if matrix.ndim != 2 or np.any(matrix < -1e-12):
        raise ValueError("channel must be a nonnegative state-by-signal matrix")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9):
        raise ValueError("every state row must be a probability distribution")
    return matrix


def best_garbling(source_channel: np.ndarray, target_channel: np.ndarray, tolerance: float = 1e-8) -> GarblingCertificate:
    """Find the row-stochastic garbling minimizing maximum channel error."""
    source = _validate_channel(source_channel)
    target = _validate_channel(target_channel)
    if source.shape[0] != target.shape[0]:
        raise ValueError("channels must describe the same states")
    states, source_signals = source.shape
    target_signals = target.shape[1]
    garbling_variables = source_signals * target_signals
    t_index = garbling_variables
    objective = np.zeros(garbling_variables + 1)
    objective[t_index] = 1.0
    equalities = []
    equality_rhs = []
    for source_signal in range(source_signals):
        row = np.zeros(garbling_variables + 1)
        start = source_signal * target_signals
        row[start : start + target_signals] = 1.0
        equalities.append(row)
        equality_rhs.append(1.0)
    inequalities = []
    inequality_rhs = []
    for state in range(states):
        for target_signal in range(target_signals):
            row = np.zeros(garbling_variables + 1)
            for source_signal in range(source_signals):
                row[source_signal * target_signals + target_signal] = source[state, source_signal]
            row[t_index] = -1.0
            inequalities.append(row)
            inequality_rhs.append(target[state, target_signal])
            inequalities.append(-row.copy())
            inequalities[-1][t_index] = -1.0
            inequality_rhs.append(-target[state, target_signal])
    solved = linprog(
        objective,
        A_ub=np.asarray(inequalities),
        b_ub=np.asarray(inequality_rhs),
        A_eq=np.asarray(equalities),
        b_eq=np.asarray(equality_rhs),
        bounds=[(0.0, 1.0)] * garbling_variables + [(0.0, None)],
        method="highs",
    )
    if not solved.success:
        raise RuntimeError(solved.message)
    garbling = solved.x[:garbling_variables].reshape(source_signals, target_signals)
    residual = float(np.max(np.abs(source @ garbling - target)))
    return GarblingCertificate(residual <= tolerance, garbling, residual)


def audit_channels(first_channel: np.ndarray, second_channel: np.ndarray, tolerance: float = 1e-8) -> ChannelAudit:
    first_to_second = best_garbling(first_channel, second_channel, tolerance)
    second_to_first = best_garbling(second_channel, first_channel, tolerance)
    if first_to_second.source_dominates_target and second_to_first.source_dominates_target:
        relation = "BLACKWELL_EQUIVALENT"
    elif first_to_second.source_dominates_target:
        relation = "FIRST_STRICTLY_MORE_INFORMATIVE"
    elif second_to_first.source_dominates_target:
        relation = "SECOND_STRICTLY_MORE_INFORMATIVE"
    else:
        relation = "INCOMPARABLE"
    return ChannelAudit(relation, first_to_second, second_to_first)


def decision_value(channel: np.ndarray, prior: np.ndarray, action_utility: np.ndarray) -> dict[str, float]:
    """Return optimal ex-ante value with and without the channel."""
    experiment = _validate_channel(channel)
    belief = np.asarray(prior, dtype=float)
    utility = np.asarray(action_utility, dtype=float)
    if belief.shape != (experiment.shape[0],) or utility.shape[1] != experiment.shape[0]:
        raise ValueError("prior or action utility has incompatible state dimension")
    belief = belief / belief.sum()
    without = float(np.max(utility @ belief))
    with_signal = 0.0
    for signal in range(experiment.shape[1]):
        state_weights = belief * experiment[:, signal]
        with_signal += float(np.max(utility @ state_weights))
    return {
        "without_channel": without,
        "with_channel": with_signal,
        "value_of_information": with_signal - without,
    }

