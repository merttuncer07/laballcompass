"""Decision-Targeted Private Release (DTPR).

The module turns a pre-declared decision score into a differentially private
action.  It also allocates a finite privacy budget across several decisions
according to operational consequence and query sensitivity.

Only the Python standard library is required.
"""

from __future__ import annotations

from dataclasses import dataclass
import bisect
import hashlib
import json
import math
import random
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class DecisionSpec:
    """Public specification for one private decision.

    ``thresholds`` must be increasing.  With n thresholds, n+1 action labels
    are required.  ``sensitivity`` is the global sensitivity of the score
    under the chosen neighboring-dataset definition.  ``consequence_weight``
    is a non-negative operational weight, not a novelty or confidence score.
    """

    name: str
    thresholds: tuple[float, ...]
    actions: tuple[str, ...]
    sensitivity: float
    consequence_weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Decision name cannot be empty")
        if len(self.actions) != len(self.thresholds) + 1:
            raise ValueError("n thresholds require n+1 actions")
        if any(b <= a for a, b in zip(self.thresholds, self.thresholds[1:])):
            raise ValueError("Thresholds must be strictly increasing")
        if self.sensitivity <= 0 or not math.isfinite(self.sensitivity):
            raise ValueError("Sensitivity must be finite and positive")
        if self.consequence_weight < 0 or not math.isfinite(self.consequence_weight):
            raise ValueError("Consequence weight must be finite and non-negative")

    def action_for(self, score: float) -> str:
        return self.actions[bisect.bisect_right(self.thresholds, score)]

    @property
    def fingerprint(self) -> str:
        """Stable handle proving which public rule produced a release."""

        payload = json.dumps(
            {
                "name": self.name,
                "thresholds": self.thresholds,
                "actions": self.actions,
                "sensitivity": self.sensitivity,
                "consequence_weight": self.consequence_weight,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class BudgetAllocation:
    epsilon_by_decision: Mapping[str, float]
    total_epsilon: float
    method: str

    @property
    def epsilon_spent(self) -> float:
        return sum(self.epsilon_by_decision.values())


@dataclass(frozen=True)
class PrivateActionRelease:
    decision: str
    action: str
    epsilon: float
    sensitivity: float
    noise_scale: float
    stability_band: int
    rule_fingerprint: str
    noisy_score: float | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "action": self.action,
            "epsilon": self.epsilon,
            "sensitivity": self.sensitivity,
            "noise_scale": self.noise_scale,
            "stability_band": self.stability_band,
            "rule_fingerprint": self.rule_fingerprint,
            "noisy_score": self.noisy_score,
        }


@dataclass(frozen=True)
class PrivateSelectionRelease:
    decision: str
    selected_action: str
    epsilon: float
    utility_sensitivity: float
    mechanism: str
    candidate_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "selected_action": self.selected_action,
            "epsilon": self.epsilon,
            "utility_sensitivity": self.utility_sensitivity,
            "mechanism": self.mechanism,
            "candidate_count": self.candidate_count,
        }


def allocate_budget(
    specs: Sequence[DecisionSpec],
    total_epsilon: float,
    method: str = "decision_weighted",
) -> BudgetAllocation:
    """Allocate a composed epsilon budget across declared decisions.

    ``decision_weighted`` minimizes a local weighted Laplace-variance proxy:

        sum_i weight_i * 2 * (sensitivity_i / epsilon_i)^2

    subject to sum epsilon_i = total_epsilon.  The solution is
    epsilon_i proportional to (weight_i * sensitivity_i^2)^(1/3).

    Zero-consequence items receive no privacy budget and therefore no release.
    ``uniform`` is provided as a transparent comparison.
    """

    if total_epsilon <= 0 or not math.isfinite(total_epsilon):
        raise ValueError("total_epsilon must be finite and positive")
    if not specs:
        raise ValueError("At least one decision specification is required")
    names = [spec.name for spec in specs]
    if len(set(names)) != len(names):
        raise ValueError("Decision names must be unique")

    if method == "uniform":
        share = total_epsilon / len(specs)
        eps = {spec.name: share for spec in specs}
    elif method == "decision_weighted":
        masses = {
            spec.name: (spec.consequence_weight * spec.sensitivity**2) ** (1.0 / 3.0)
            if spec.consequence_weight > 0
            else 0.0
            for spec in specs
        }
        total_mass = sum(masses.values())
        if total_mass <= 0:
            raise ValueError("At least one decision must have positive consequence weight")
        eps = {name: total_epsilon * mass / total_mass for name, mass in masses.items()}
    else:
        raise ValueError("method must be 'uniform' or 'decision_weighted'")

    return BudgetAllocation(eps, total_epsilon, method)


def _laplace(rng: random.Random, scale: float) -> float:
    """Sample Laplace(0, scale) through a stable inverse CDF."""

    if scale <= 0 or not math.isfinite(scale):
        raise ValueError("Laplace scale must be finite and positive")
    u = rng.random() - 0.5
    return -scale * math.copysign(math.log1p(-2.0 * abs(u)), u)


def _stability_band(noisy_score: float, thresholds: Sequence[float], scale: float) -> int:
    """Coarse, post-processed distance from the nearest decision boundary.

    Band 0 means closer than one noise scale, band 1 means one-to-two scales,
    and band 2 means at least two scales.  It is computed only from the DP
    release, so it consumes no additional privacy budget.
    """

    if not thresholds:
        return 2
    distance = min(abs(noisy_score - boundary) for boundary in thresholds)
    return min(2, int(distance / scale))


def _sample_exponential_mechanism(
    rng: random.Random,
    utilities: Mapping[str, float],
    epsilon: float,
    utility_sensitivity: float,
) -> str:
    """Sample an action with probability proportional to exp(epsilon*u/2Δu)."""

    if not utilities:
        raise ValueError("At least one candidate action is required")
    if epsilon <= 0 or not math.isfinite(epsilon):
        raise ValueError("epsilon must be finite and positive")
    if utility_sensitivity <= 0 or not math.isfinite(utility_sensitivity):
        raise ValueError("utility_sensitivity must be finite and positive")
    if any(not math.isfinite(value) for value in utilities.values()):
        raise ValueError("All utilities must be finite")

    coefficient = epsilon / (2.0 * utility_sensitivity)
    log_weights = {action: coefficient * utility for action, utility in utilities.items()}
    shift = max(log_weights.values())
    weights = {action: math.exp(log_weight - shift) for action, log_weight in log_weights.items()}
    draw = rng.random() * sum(weights.values())
    cumulative = 0.0
    for action, weight in weights.items():
        cumulative += weight
        if draw <= cumulative:
            return action
    return next(reversed(weights))


class DecisionTargetedPrivateRelease:
    """Release private actions while keeping a running composition ledger."""

    def __init__(self, total_epsilon: float, seed: int | None = None) -> None:
        if total_epsilon <= 0 or not math.isfinite(total_epsilon):
            raise ValueError("total_epsilon must be finite and positive")
        self.total_epsilon = total_epsilon
        self._remaining_epsilon = total_epsilon
        # Production releases use the operating system's cryptographic random
        # source.  A seeded PRNG exists only for reproducible construction
        # evaluations and tests.
        self._rng = random.SystemRandom() if seed is None else random.Random(seed)
        self._ledger: list[dict[str, object]] = []

    @property
    def remaining_epsilon(self) -> float:
        return self._remaining_epsilon

    @property
    def ledger(self) -> tuple[Mapping[str, object], ...]:
        return tuple(self._ledger)

    def release(
        self,
        spec: DecisionSpec,
        true_score: float,
        epsilon: float,
        *,
        expose_noisy_score: bool = False,
    ) -> PrivateActionRelease:
        if epsilon <= 0 or not math.isfinite(epsilon):
            raise ValueError("epsilon must be finite and positive")
        if epsilon > self._remaining_epsilon + 1e-12:
            raise RuntimeError("Privacy budget exhausted")
        if not math.isfinite(true_score):
            raise ValueError("true_score must be finite")

        scale = spec.sensitivity / epsilon
        noisy_score = true_score + _laplace(self._rng, scale)
        action = spec.action_for(noisy_score)
        band = _stability_band(noisy_score, spec.thresholds, scale)

        self._remaining_epsilon = max(0.0, self._remaining_epsilon - epsilon)
        release = PrivateActionRelease(
            decision=spec.name,
            action=action,
            epsilon=epsilon,
            sensitivity=spec.sensitivity,
            noise_scale=scale,
            stability_band=band,
            rule_fingerprint=spec.fingerprint,
            noisy_score=noisy_score if expose_noisy_score else None,
        )
        self._ledger.append(release.as_dict())
        return release

    def release_plan(
        self,
        specs: Sequence[DecisionSpec],
        true_scores: Mapping[str, float],
        allocation: BudgetAllocation,
        *,
        expose_noisy_scores: bool = False,
    ) -> list[PrivateActionRelease]:
        if allocation.epsilon_spent > self._remaining_epsilon + 1e-12:
            raise RuntimeError("Allocation exceeds remaining privacy budget")

        releases: list[PrivateActionRelease] = []
        for spec in specs:
            epsilon = allocation.epsilon_by_decision.get(spec.name, 0.0)
            if epsilon <= 0:
                continue
            if spec.name not in true_scores:
                raise KeyError(f"Missing score for decision: {spec.name}")
            releases.append(
                self.release(
                    spec,
                    true_scores[spec.name],
                    epsilon,
                    expose_noisy_score=expose_noisy_scores,
                )
            )
        return releases

    def release_argmax(
        self,
        decision_name: str,
        utilities: Mapping[str, float],
        epsilon: float,
        utility_sensitivity: float,
    ) -> PrivateSelectionRelease:
        """Release only the selected action through the exponential mechanism."""

        if epsilon > self._remaining_epsilon + 1e-12:
            raise RuntimeError("Privacy budget exhausted")
        selected = _sample_exponential_mechanism(
            self._rng, utilities, epsilon, utility_sensitivity
        )
        self._remaining_epsilon = max(0.0, self._remaining_epsilon - epsilon)
        release = PrivateSelectionRelease(
            decision=decision_name,
            selected_action=selected,
            epsilon=epsilon,
            utility_sensitivity=utility_sensitivity,
            mechanism="exponential",
            candidate_count=len(utilities),
        )
        self._ledger.append(release.as_dict())
        return release

    def release_top_k(
        self,
        decision_name: str,
        utilities: Mapping[str, float],
        k: int,
        total_epsilon: float,
        utility_sensitivity: float,
    ) -> list[PrivateSelectionRelease]:
        """Select k distinct actions; sequential releases compose to total_epsilon."""

        if not 1 <= k <= len(utilities):
            raise ValueError("k must be between 1 and the number of candidate actions")
        if total_epsilon > self._remaining_epsilon + 1e-12:
            raise RuntimeError("Privacy budget exhausted")
        per_slot = total_epsilon / k
        remaining = dict(utilities)
        releases: list[PrivateSelectionRelease] = []
        for slot in range(1, k + 1):
            release = self.release_argmax(
                f"{decision_name}:slot_{slot}",
                remaining,
                per_slot,
                utility_sensitivity,
            )
            releases.append(release)
            del remaining[release.selected_action]
        return releases


def count_score(values: Iterable[bool]) -> int:
    """Count a boolean condition; add/remove global sensitivity is one."""

    return sum(bool(value) for value in values)
