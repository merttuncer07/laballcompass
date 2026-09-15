"""Binary Persuasion Information-Structure Designer (BPISD) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class SignalPolicy:
    signal: str
    probability: float
    posterior_state_one: float
    receiver_action: str
    probability_given_state_zero: float
    probability_given_state_one: float
    sender_expected_payoff: float
    receiver_expected_payoff: float


@dataclass(frozen=True)
class PersuasionDesign:
    prior_state_one: float
    signals: tuple[SignalPolicy, ...]
    bayes_posterior_mean: float
    bayes_plausibility_residual: float
    optimized_sender_value: float
    no_information_sender_value: float
    full_revelation_sender_value: float
    persuasion_gain_over_no_information: float
    status: str

    def to_dict(self) -> dict:
        payload = asdict(self); payload["signals"] = [asdict(item) for item in self.signals]; return payload


def design_binary_persuasion(
    *, prior_state_one: float, action_names: Sequence[str],
    receiver_payoffs: Sequence[Sequence[float]], sender_payoffs: Sequence[Sequence[float]],
    posterior_grid_size: int = 1001, tie_break_sender_favorable: bool = True,
) -> PersuasionDesign:
    """Concavify sender value over binary-state posteriors and return an implementable signal channel."""
    if not np.isfinite(prior_state_one) or not 0 < prior_state_one < 1:
        raise ValueError("prior_state_one must lie strictly between zero and one")
    names = tuple(action_names); r = np.asarray(receiver_payoffs, float); s = np.asarray(sender_payoffs, float)
    if not names or len(set(names)) != len(names) or r.shape != (len(names), 2) or s.shape != r.shape:
        raise ValueError("unique action names and action-by-two-state payoff matrices are required")
    if not np.all(np.isfinite(r)) or not np.all(np.isfinite(s)) or posterior_grid_size < 3:
        raise ValueError("payoffs must be finite and grid size at least three")
    q = np.unique(np.append(np.linspace(0, 1, posterior_grid_size), prior_state_one))
    receiver_value = r[:, 0, None] * (1 - q) + r[:, 1, None] * q
    sender_value_by_action = s[:, 0, None] * (1 - q) + s[:, 1, None] * q
    chosen = np.zeros(q.size, dtype=int)
    for index in range(q.size):
        best_receiver = np.max(receiver_value[:, index]); eligible = np.where(np.isclose(receiver_value[:, index], best_receiver))[0]
        chosen[index] = eligible[np.argmax(sender_value_by_action[eligible, index])] if tie_break_sender_favorable else eligible[0]
    sender_curve = sender_value_by_action[chosen, np.arange(q.size)]
    result = linprog(-sender_curve, A_eq=np.vstack([np.ones(q.size), q]), b_eq=[1, prior_state_one],
                     bounds=(0, None), method="highs")
    if not result.success: raise RuntimeError("persuasion linear program failed")
    active = np.where(result.x > 1e-9)[0]; policies = []
    for number, index in enumerate(active):
        probability = float(result.x[index]); posterior = float(q[index]); action = int(chosen[index])
        policies.append(SignalPolicy(
            f"S{number+1}", probability, posterior, names[action],
            probability * (1 - posterior) / (1 - prior_state_one), probability * posterior / prior_state_one,
            float(sender_curve[index]), float(receiver_value[action, index]),
        ))
    prior_index = int(np.where(q == prior_state_one)[0][0]); no_info = float(sender_curve[prior_index])
    full = float((1-prior_state_one)*sender_curve[0] + prior_state_one*sender_curve[-1])
    posterior_mean = float(sum(item.probability * item.posterior_state_one for item in policies))
    optimized = float(-result.fun)
    return PersuasionDesign(prior_state_one, tuple(policies), posterior_mean, abs(posterior_mean-prior_state_one),
                            optimized, no_info, full, optimized-no_info, "BAYES_PLAUSIBLE_CHANNEL")
