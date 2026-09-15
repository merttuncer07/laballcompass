"""Basin-targeted teaching with an MCES-style authority firewall.

This is a bounded research component, not a deployment controller.  It searches
for a designed example whose one-shot gradient update moves a small learner into
a better post-retraining optimizer basin.  Immediate-loss-greedy teaching is
evaluated at the exact same intervention norm.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

import numpy as np


Array = np.ndarray


@dataclass(frozen=True)
class AuthorityContext:
    model_class_covered: bool
    optimizer_scope_matches: bool
    candidate_sensor_map_complete: bool
    evidence_fresh: bool
    objective_authorized: bool
    tolerance_authorized: bool
    recovery_observable: bool


@dataclass(frozen=True)
class AuthorityDecision:
    action: str
    reasons: tuple[str, ...]


def authority_gate(context: AuthorityContext) -> AuthorityDecision:
    checks = {
        "model-class coverage is incomplete": context.model_class_covered,
        "optimizer scope does not match": context.optimizer_scope_matches,
        "candidate sensor map is incomplete": context.candidate_sensor_map_complete,
        "evidence is stale": context.evidence_fresh,
        "target objective lacks authority": context.objective_authorized,
        "intervention tolerance lacks authority": context.tolerance_authorized,
        "post-intervention recovery is not observable": context.recovery_observable,
    }
    failures = tuple(message for message, passed in checks.items() if not passed)
    return AuthorityDecision("ABSTAIN" if failures else "SEARCH", failures)


@dataclass(frozen=True)
class TrainingResult:
    theta: Array
    loss: float
    steps: int


@dataclass(frozen=True)
class CandidateDirection:
    x: tuple[float, float]
    y: float
    direction: Array
    immediate_slope: float


@dataclass(frozen=True)
class InterventionOutcome:
    candidate: CandidateDirection
    norm: float
    immediate_loss: float
    final_loss: float
    success: bool


@dataclass(frozen=True)
class TeachingComparison:
    authority: AuthorityDecision
    hidden: int
    source_seed: int
    bad_loss: float
    basin: InterventionOutcome | None
    greedy_at_basin_norm: InterventionOutcome | None
    candidates_evaluated: int
    failure: str | None

    def to_jsonable(self) -> dict:
        def outcome(value: InterventionOutcome | None):
            if value is None:
                return None
            return {
                "x": list(value.candidate.x),
                "y": value.candidate.y,
                "immediate_slope": value.candidate.immediate_slope,
                "norm": value.norm,
                "immediate_loss": value.immediate_loss,
                "final_loss": value.final_loss,
                "success": value.success,
            }

        return {
            "authority": asdict(self.authority),
            "hidden": self.hidden,
            "source_seed": self.source_seed,
            "bad_loss": self.bad_loss,
            "basin": outcome(self.basin),
            "greedy_at_basin_norm": outcome(self.greedy_at_basin_norm),
            "candidates_evaluated": self.candidates_evaluated,
            "failure": self.failure,
        }


class TinyTanhXOR:
    """One-hidden-layer tanh network with 4H+1 packed parameters."""

    X = np.asarray([[-1.0, -1.0], [-1.0, 1.0], [1.0, -1.0], [1.0, 1.0]])
    Y = np.asarray([-1.0, 1.0, 1.0, -1.0])

    def __init__(self, hidden: int):
        if hidden < 2:
            raise ValueError("XOR requires at least two hidden units")
        self.hidden = hidden
        self.parameter_count = 4 * hidden + 1

    def unpack(self, theta: Array) -> tuple[Array, Array, Array, float]:
        theta = np.asarray(theta, dtype=float)
        if theta.shape != (self.parameter_count,):
            raise ValueError(f"expected {self.parameter_count} parameters")
        h = self.hidden
        w1 = theta[: 2 * h].reshape(h, 2)
        b1 = theta[2 * h : 3 * h]
        w2 = theta[3 * h : 4 * h]
        b2 = float(theta[-1])
        return w1, b1, w2, b2

    def forward(self, theta: Array, x: Array) -> tuple[Array, Array]:
        w1, b1, w2, b2 = self.unpack(theta)
        x = np.atleast_2d(np.asarray(x, dtype=float))
        hidden = np.tanh(x @ w1.T + b1)
        output = np.tanh(hidden @ w2 + b2)
        return output, hidden

    def loss(self, theta: Array, x: Array | None = None, y: Array | None = None) -> float:
        x = self.X if x is None else np.atleast_2d(np.asarray(x, dtype=float))
        y = self.Y if y is None else np.atleast_1d(np.asarray(y, dtype=float))
        prediction, _ = self.forward(theta, x)
        return float(0.5 * np.mean((prediction - y) ** 2))

    def gradient(self, theta: Array, x: Array | None = None, y: Array | None = None) -> Array:
        x = self.X if x is None else np.atleast_2d(np.asarray(x, dtype=float))
        y = self.Y if y is None else np.atleast_1d(np.asarray(y, dtype=float))
        prediction, hidden = self.forward(theta, x)
        w1, _b1, w2, _b2 = self.unpack(theta)
        dout = (prediction - y) * (1.0 - prediction**2) / len(y)
        grad_w2 = hidden.T @ dout
        grad_b2 = float(np.sum(dout))
        dhidden = dout[:, None] * w2[None, :] * (1.0 - hidden**2)
        grad_w1 = dhidden.T @ x
        grad_b1 = np.sum(dhidden, axis=0)
        return np.concatenate([grad_w1.ravel(), grad_b1, grad_w2, [grad_b2]])

    def batch_loss_and_gradient(self, thetas: Array) -> tuple[Array, Array]:
        """Vectorized full-XOR loss/gradient for many parameter states."""
        states = np.atleast_2d(np.asarray(thetas, dtype=float))
        h = self.hidden
        w1 = states[:, : 2 * h].reshape(-1, h, 2)
        b1 = states[:, 2 * h : 3 * h]
        w2 = states[:, 3 * h : 4 * h]
        b2 = states[:, -1]
        hidden = np.tanh(np.einsum("ni,khi->knh", self.X, w1) + b1[:, None, :])
        prediction = np.tanh(np.einsum("knh,kh->kn", hidden, w2) + b2[:, None])
        losses = 0.5 * np.mean((prediction - self.Y[None, :]) ** 2, axis=1)
        dout = (prediction - self.Y[None, :]) * (1.0 - prediction**2) / len(self.Y)
        grad_w2 = np.einsum("knh,kn->kh", hidden, dout)
        grad_b2 = np.sum(dout, axis=1)
        dhidden = dout[:, :, None] * w2[:, None, :] * (1.0 - hidden**2)
        grad_w1 = np.einsum("knh,ni->khi", dhidden, self.X)
        grad_b1 = np.sum(dhidden, axis=1)
        gradients = np.concatenate(
            [grad_w1.reshape(len(states), -1), grad_b1, grad_w2, grad_b2[:, None]],
            axis=1,
        )
        return losses, gradients

    def batch_train(
        self,
        thetas: Array,
        *,
        learning_rate: float = 0.12,
        max_steps: int = 2500,
    ) -> tuple[Array, Array]:
        states = np.atleast_2d(np.asarray(thetas, dtype=float)).copy()
        for _ in range(max_steps):
            _losses, gradients = self.batch_loss_and_gradient(states)
            states -= learning_rate * gradients
        losses, _gradients = self.batch_loss_and_gradient(states)
        return states, losses

    def initialize(self, seed: int, scale: float = 1.5) -> Array:
        return np.random.default_rng(seed).normal(0.0, scale, self.parameter_count)

    def train(
        self,
        theta: Array,
        *,
        learning_rate: float = 0.12,
        max_steps: int = 3500,
        tolerance: float = 1e-8,
    ) -> TrainingResult:
        state = np.asarray(theta, dtype=float).copy()
        previous = self.loss(state)
        for step in range(1, max_steps + 1):
            state -= learning_rate * self.gradient(state)
            current = self.loss(state)
            if current <= tolerance or abs(previous - current) <= tolerance * 1e-2:
                return TrainingResult(state, current, step)
            previous = current
        return TrainingResult(state, previous, max_steps)


def designed_candidates(
    model: TinyTanhXOR,
    theta: Array,
    *,
    seed: int,
    random_count: int = 96,
    extent: float = 2.25,
) -> list[CandidateDirection]:
    rng = np.random.default_rng(seed)
    points = rng.uniform(-extent, extent, size=(random_count, 2))
    anchors = np.asarray([[a, b] for a in (-2.0, -1.0, 0.0, 1.0, 2.0) for b in (-2.0, -1.0, 0.0, 1.0, 2.0)])
    points = np.vstack([points, anchors])
    full_gradient = model.gradient(theta)
    candidates: list[CandidateDirection] = []
    for point in points:
        for target in (-1.0, 1.0):
            gradient = model.gradient(theta, point[None, :], np.asarray([target]))
            magnitude = float(np.linalg.norm(gradient))
            if magnitude <= 1e-12:
                continue
            update_direction = -gradient / magnitude
            slope = float(full_gradient @ update_direction)
            candidates.append(CandidateDirection(tuple(map(float, point)), target, update_direction, slope))
    return candidates


def apply_and_retrain(
    model: TinyTanhXOR,
    theta: Array,
    candidate: CandidateDirection,
    norm: float,
    *,
    success_loss: float,
    retrain_steps: int,
) -> InterventionOutcome:
    intervened = np.asarray(theta) + norm * candidate.direction
    immediate = model.loss(intervened)
    trained = model.train(intervened, max_steps=retrain_steps)
    return InterventionOutcome(candidate, float(norm), immediate, trained.loss, trained.loss <= success_loss)


def first_crossing(
    model: TinyTanhXOR,
    theta: Array,
    candidate: CandidateDirection,
    *,
    norm_grid: Sequence[float],
    success_loss: float,
    retrain_steps: int,
    bisection_steps: int = 9,
) -> InterventionOutcome | None:
    lower = 0.0
    upper: float | None = None
    best: InterventionOutcome | None = None
    for norm in norm_grid:
        outcome = apply_and_retrain(model, theta, candidate, float(norm), success_loss=success_loss, retrain_steps=retrain_steps)
        if outcome.success:
            upper, best = float(norm), outcome
            break
        lower = float(norm)
    if upper is None:
        return None
    for _ in range(bisection_steps):
        midpoint = 0.5 * (lower + upper)
        outcome = apply_and_retrain(model, theta, candidate, midpoint, success_loss=success_loss, retrain_steps=retrain_steps)
        if outcome.success:
            upper, best = midpoint, outcome
        else:
            lower = midpoint
    return best


def compare_teachers(
    model: TinyTanhXOR,
    bad_theta: Array,
    *,
    source_seed: int,
    authority: AuthorityContext,
    candidate_seed: int,
    random_candidates: int = 96,
    norm_grid: Sequence[float] = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0),
    success_loss: float = 1e-3,
    retrain_steps: int = 800,
) -> TeachingComparison:
    decision = authority_gate(authority)
    bad_loss = model.loss(bad_theta)
    if decision.action != "SEARCH":
        return TeachingComparison(decision, model.hidden, source_seed, bad_loss, None, None, 0, "authority_gate")

    candidates = designed_candidates(model, bad_theta, seed=candidate_seed, random_count=random_candidates)
    if not candidates:
        return TeachingComparison(decision, model.hidden, source_seed, bad_loss, None, None, 0, "no_candidate_gradient")

    # Immediate-loss greedy: most negative directional derivative per unit norm.
    greedy = min(candidates, key=lambda candidate: candidate.immediate_slope)

    # Evaluate all candidate rays in parallel.  This preserves the empirical
    # post-retraining basin test while avoiding one Python training loop per ray.
    directions = np.stack([candidate.direction for candidate in candidates])
    first_success: dict[int, tuple[float, float, float]] = {}
    previous_norm = 0.0
    first_success_norm: float | None = None
    first_success_lower = 0.0
    for norm in norm_grid:
        initial = np.asarray(bad_theta)[None, :] + float(norm) * directions
        immediate, _ = model.batch_loss_and_gradient(initial)
        _trained, final = model.batch_train(initial, max_steps=retrain_steps)
        newly_successful = np.flatnonzero(final <= success_loss)
        for index in newly_successful:
            first_success.setdefault(int(index), (float(norm), float(immediate[index]), float(final[index])))
        if first_success and first_success_norm is None:
            first_success_norm = float(norm)
            first_success_lower = previous_norm
            break
        previous_norm = float(norm)
    if not first_success:
        return TeachingComparison(decision, model.hidden, source_seed, bad_loss, None, None, len(candidates), "no_crossing_within_budget")

    # Refine every ray that crossed at the earliest coarse norm, then select the
    # lowest empirical threshold.  Later coarse bins cannot beat its lower edge.
    crossings: list[InterventionOutcome] = []
    for index, (coarse_norm, _immediate, _final) in first_success.items():
        if coarse_norm != first_success_norm:
            continue
        crossing = first_crossing(
            model,
            bad_theta,
            candidates[index],
            norm_grid=(first_success_lower, coarse_norm),
            success_loss=success_loss,
            retrain_steps=retrain_steps,
            bisection_steps=7,
        )
        if crossing is not None:
            crossings.append(crossing)
    basin = min(crossings, key=lambda outcome: outcome.norm)
    greedy_outcome = apply_and_retrain(
        model,
        bad_theta,
        greedy,
        basin.norm,
        success_loss=success_loss,
        retrain_steps=retrain_steps,
    )
    return TeachingComparison(decision, model.hidden, source_seed, bad_loss, basin, greedy_outcome, len(candidates), None)


def locate_bad_basins(
    hidden: int,
    seeds: Iterable[int],
    *,
    count: int,
    bad_loss_floor: float = 0.08,
    max_loss: float = 0.6,
) -> list[tuple[int, TrainingResult]]:
    model = TinyTanhXOR(hidden)
    found: list[tuple[int, TrainingResult]] = []
    for seed in seeds:
        result = model.train(model.initialize(seed))
        if bad_loss_floor <= result.loss <= max_loss:
            found.append((seed, result))
            if len(found) >= count:
                break
    return found


FULL_AUTHORITY = AuthorityContext(True, True, True, True, True, True, True)
