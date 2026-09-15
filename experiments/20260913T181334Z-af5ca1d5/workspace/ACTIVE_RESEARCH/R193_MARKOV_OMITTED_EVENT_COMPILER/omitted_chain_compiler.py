from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def project_simplex(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u)
    candidates = np.flatnonzero(u * np.arange(1, len(u) + 1) > cssv - 1.0)
    if len(candidates) == 0:
        return np.full_like(v, 1.0 / len(v))
    rho = int(candidates[-1])
    theta = (cssv[rho] - 1.0) / (rho + 1)
    return np.maximum(v - theta, 0.0)


def row_stochastic(matrix: np.ndarray) -> np.ndarray:
    return np.vstack([project_simplex(row) for row in np.asarray(matrix, dtype=float)])


def observed_transition(p: np.ndarray, omission_rate: float) -> np.ndarray:
    """Transition among retained records under independent event omission."""
    p = np.asarray(p, dtype=float)
    eye = np.eye(p.shape[0])
    return (1.0 - omission_rate) * p @ np.linalg.inv(eye - omission_rate * p)


def invert_observed_transition(
    q: np.ndarray, omission_rate: float, project: bool = True
) -> np.ndarray:
    """Algebraic inverse of the geometric omission resolvent."""
    q = np.asarray(q, dtype=float)
    a = (1.0 - omission_rate) * np.eye(q.shape[0]) + omission_rate * q
    p = np.linalg.solve(a, q)
    return row_stochastic(p) if project else p


def transition_counts(states: np.ndarray, n_states: int) -> np.ndarray:
    counts = np.zeros((n_states, n_states), dtype=float)
    np.add.at(counts, (states[:-1], states[1:]), 1.0)
    return counts


def estimate_transition(states: np.ndarray, n_states: int, alpha: float) -> np.ndarray:
    counts = transition_counts(states, n_states) + float(alpha)
    return counts / counts.sum(axis=1, keepdims=True)


def log_loss(p: np.ndarray, states: np.ndarray) -> float:
    probs = p[states[:-1], states[1:]]
    return float(-np.mean(np.log(np.maximum(probs, 1e-15))))


@dataclass
class OmittedEventChainCompiler:
    """Compile retained-record transitions back into true one-step dynamics.

    `omission_rate` is not identifiable from retained states alone. It must come
    from sampling configuration, sequence numbers, heartbeat audits or another
    external calibration source.
    """

    omission_rate: float
    alphas: tuple[float, ...] = (0.05, 0.25, 1.0, 4.0, 12.0)
    # Never deploy a mathematically full finite-sample inverse: simplex
    # projection can create false structural zeros. 0.995 retains a small
    # observed-chain support floor while remaining effectively fully inverted.
    inversion_strengths: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 0.90, 0.97, 0.995)
    dev_fraction: float = 0.30

    transition_: np.ndarray | None = None
    observed_transition_: np.ndarray | None = None
    selected_alpha_: float | None = None
    selected_strength_: float | None = None
    condition_number_: float | None = None
    dev_log_loss_: float | None = None

    def __post_init__(self):
        if not 0.0 <= self.omission_rate < 1.0:
            raise ValueError("omission_rate must be in [0,1)")

    def _candidate(self, q: np.ndarray, strength: float) -> np.ndarray:
        full = invert_observed_transition(q, self.omission_rate, project=True)
        return row_stochastic((1.0 - strength) * q + strength * full)

    def fit(self, retained_states: np.ndarray, n_states: int | None = None):
        retained_states = np.asarray(retained_states, dtype=np.int64)
        if len(retained_states) < 20:
            raise ValueError("at least 20 retained states are required")
        if n_states is None:
            n_states = int(retained_states.max()) + 1
        split = max(10, int(round(len(retained_states) * (1.0 - self.dev_fraction))))
        split = min(split, len(retained_states) - 5)
        fit_states = retained_states[:split]
        dev_states = retained_states[split - 1 :]

        best = (float("inf"), None, None)
        for alpha in self.alphas:
            q = estimate_transition(fit_states, n_states, alpha)
            for strength in self.inversion_strengths:
                p = self._candidate(q, strength)
                q_pred = observed_transition(p, self.omission_rate)
                loss = log_loss(q_pred, dev_states)
                # Prefer less inversion when losses are numerically tied.
                key = (loss, strength)
                if key < (best[0], best[2] if best[2] is not None else float("inf")):
                    best = (loss, alpha, strength)

        self.dev_log_loss_, self.selected_alpha_, self.selected_strength_ = best
        q_full = estimate_transition(retained_states, n_states, self.selected_alpha_)
        self.observed_transition_ = q_full
        self.transition_ = self._candidate(q_full, self.selected_strength_)
        a = (1.0 - self.omission_rate) * np.eye(n_states) + self.omission_rate * q_full
        self.condition_number_ = float(np.linalg.cond(a))
        return self

    def predict_proba(self, states: np.ndarray | list[int]) -> np.ndarray:
        if self.transition_ is None:
            raise RuntimeError("fit must be called first")
        return self.transition_[np.asarray(states, dtype=np.int64)]

    def diagnostics(self) -> dict:
        return {
            "omission_rate": self.omission_rate,
            "selected_alpha": self.selected_alpha_,
            "selected_inversion_strength": self.selected_strength_,
            "inverse_condition_number": self.condition_number_,
            "observed_dev_log_loss": self.dev_log_loss_,
            "identifiability_warning": (
                "omission_rate is externally supplied; retained states alone do not identify it"
            ),
        }
