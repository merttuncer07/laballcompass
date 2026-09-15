"""Local basin-edge estimator for Basin Authority Teacher v0.0.2."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

from basin_authority_teacher import (
    FULL_AUTHORITY,
    AuthorityContext,
    CandidateDirection,
    TinyTanhXOR,
    authority_gate,
    designed_candidates,
)


@dataclass(frozen=True)
class EdgeEstimate:
    direction: np.ndarray
    lower_bad_fraction: float
    upper_good_fraction: float
    boundary_distance: float
    retraining_units: int


@dataclass(frozen=True)
class RankedSearchOutcome:
    method: str
    candidates_tested: int
    norms_tested: tuple[float, ...]
    evaluation_units: int
    success: bool
    minimum_norm: float | None
    final_loss: float | None
    immediate_loss: float | None
    x: tuple[float, float] | None
    y: float | None
    immediate_slope: float | None


@dataclass(frozen=True)
class EdgeComparison:
    hidden: int
    bad_seed: int
    bad_loss: float
    authority_action: str
    authority_reasons: tuple[str, ...]
    total_budget_per_method: int
    estimator_units: int
    edge: RankedSearchOutcome | None
    greedy: RankedSearchOutcome | None
    edge_advantage: bool
    failure: str | None
    edge_estimate: EdgeEstimate | None

    def to_jsonable(self) -> dict:
        result = asdict(self)
        if self.edge_estimate is not None:
            result["edge_estimate"]["direction"] = self.edge_estimate.direction.tolist()
        return result


def estimate_edge(
    model: TinyTanhXOR,
    bad_theta: np.ndarray,
    good_theta: np.ndarray,
    *,
    success_loss: float = 1e-3,
    retrain_steps: int = 800,
    bisection_steps: int = 6,
) -> EdgeEstimate:
    if model.loss(good_theta) > success_loss:
        raise ValueError("good reference is not inside the declared target basin")
    displacement = np.asarray(good_theta) - np.asarray(bad_theta)
    length = float(np.linalg.norm(displacement))
    if length <= 1e-12:
        raise ValueError("bad and good references are indistinguishable")
    direction = displacement / length
    lower, upper = 0.0, 1.0
    for _ in range(bisection_steps):
        midpoint = 0.5 * (lower + upper)
        initial = np.asarray(bad_theta) + midpoint * displacement
        trained = model.train(initial, max_steps=retrain_steps)
        if trained.loss <= success_loss:
            upper = midpoint
        else:
            lower = midpoint
    return EdgeEstimate(direction, lower, upper, upper * length, bisection_steps)


def rank_candidates(
    candidates: Sequence[CandidateDirection],
    *,
    method: str,
    edge_direction: np.ndarray | None = None,
) -> list[CandidateDirection]:
    if method == "greedy":
        return sorted(candidates, key=lambda item: item.immediate_slope)
    if method == "edge":
        if edge_direction is None:
            raise ValueError("edge ranking requires an edge direction")
        return sorted(candidates, key=lambda item: float(item.direction @ edge_direction), reverse=True)
    raise ValueError(f"unknown ranking method: {method}")


def soft_mode_geometry(
    model: TinyTanhXOR,
    theta: np.ndarray,
    *,
    epsilon: float = 1e-4,
    modes: int = 4,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Return low-curvature functional modes around a bad optimizer state.

    The Hessian is symmetrized and modes that are numerically null are skipped,
    because tanh-network parameter symmetries can otherwise masquerade as an
    escape direction.  Cost is recorded as gradient evaluations, not retrains.
    """
    state = np.asarray(theta, dtype=float)
    hessian = np.zeros((len(state), len(state)))
    for column in range(len(state)):
        plus = state.copy(); plus[column] += epsilon
        minus = state.copy(); minus[column] -= epsilon
        hessian[:, column] = (model.gradient(plus) - model.gradient(minus)) / (2.0 * epsilon)
    hessian = 0.5 * (hessian + hessian.T)
    values, vectors = np.linalg.eigh(hessian)
    eligible = np.flatnonzero(np.abs(values) > 1e-6)
    if len(eligible) == 0:
        raise ValueError("no non-null local curvature modes")
    chosen = eligible[np.argsort(np.abs(values[eligible]))[: min(modes, len(eligible))]]
    return values[chosen], vectors[:, chosen], 2 * len(state)


def rank_by_soft_modes(
    model: TinyTanhXOR,
    theta: np.ndarray,
    candidates: Sequence[CandidateDirection],
    modes: np.ndarray,
    *,
    epsilon: float = 1e-4,
) -> list[CandidateDirection]:
    base_output, _ = model.forward(theta, model.X)

    def score(item: CandidateDirection) -> float:
        soft_projection = float(np.linalg.norm(modes.T @ item.direction))
        changed_output, _ = model.forward(np.asarray(theta) + epsilon * item.direction, model.X)
        functional_motion = float(np.linalg.norm((changed_output - base_output) / epsilon))
        return soft_projection * functional_motion

    return sorted(candidates, key=score, reverse=True)


def evaluate_ranked(
    model: TinyTanhXOR,
    bad_theta: np.ndarray,
    ranked: Sequence[CandidateDirection],
    *,
    method: str,
    candidate_limit: int,
    norms: Sequence[float],
    success_loss: float,
    retrain_steps: int,
) -> RankedSearchOutcome:
    selected = list(ranked[:candidate_limit])
    if not selected:
        return RankedSearchOutcome(method, 0, tuple(norms), 0, False, None, None, None, None, None, None)
    initial_states = []
    metadata = []
    for candidate in selected:
        for norm in norms:
            initial_states.append(np.asarray(bad_theta) + float(norm) * candidate.direction)
            metadata.append((candidate, float(norm)))
    states = np.stack(initial_states)
    immediate, _ = model.batch_loss_and_gradient(states)
    _trained, final = model.batch_train(states, max_steps=retrain_steps)
    successful = np.flatnonzero(final <= success_loss)
    if len(successful) == 0:
        return RankedSearchOutcome(method, len(selected), tuple(norms), len(states), False, None, None, None, None, None, None)
    best_index = min(successful, key=lambda index: (metadata[int(index)][1], float(final[int(index)])))
    candidate, norm = metadata[int(best_index)]
    return RankedSearchOutcome(
        method,
        len(selected),
        tuple(norms),
        len(states),
        True,
        norm,
        float(final[int(best_index)]),
        float(immediate[int(best_index)]),
        candidate.x,
        candidate.y,
        candidate.immediate_slope,
    )


def compare_edge_and_greedy(
    model: TinyTanhXOR,
    bad_theta: np.ndarray,
    good_theta: np.ndarray,
    *,
    bad_seed: int,
    candidate_seed: int,
    authority: AuthorityContext = FULL_AUTHORITY,
    total_budget: int = 40,
    random_candidates: int = 36,
    norms: Sequence[float] = (0.5, 1.0, 1.5, 2.0, 3.0),
    retrain_steps: int = 800,
    bisection_steps: int = 6,
    success_loss: float = 1e-3,
) -> EdgeComparison:
    decision = authority_gate(authority)
    bad_loss = model.loss(bad_theta)
    if decision.action != "SEARCH":
        return EdgeComparison(model.hidden, bad_seed, bad_loss, decision.action, decision.reasons, total_budget, 0, None, None, False, "authority_gate", None)
    try:
        edge_estimate = estimate_edge(
            model,
            bad_theta,
            good_theta,
            success_loss=success_loss,
            retrain_steps=retrain_steps,
            bisection_steps=bisection_steps,
        )
    except ValueError as error:
        return EdgeComparison(model.hidden, bad_seed, bad_loss, "ABSTAIN", (str(error),), total_budget, 0, None, None, False, "edge_estimation", None)

    candidates = designed_candidates(model, bad_theta, seed=candidate_seed, random_count=random_candidates)
    units_per_candidate = len(norms)
    # One verified-good reference is charged to this comparison in addition to
    # the bisection probes, even though a deployment may amortize it.
    estimator_units = edge_estimate.retraining_units + 1
    edge_limit = max(0, (total_budget - estimator_units) // units_per_candidate)
    greedy_limit = total_budget // units_per_candidate
    edge_ranked = rank_candidates(candidates, method="edge", edge_direction=edge_estimate.direction)
    greedy_ranked = rank_candidates(candidates, method="greedy")
    edge = evaluate_ranked(
        model,
        bad_theta,
        edge_ranked,
        method="edge",
        candidate_limit=edge_limit,
        norms=norms,
        success_loss=success_loss,
        retrain_steps=retrain_steps,
    )
    greedy = evaluate_ranked(
        model,
        bad_theta,
        greedy_ranked,
        method="greedy",
        candidate_limit=greedy_limit,
        norms=norms,
        success_loss=success_loss,
        retrain_steps=retrain_steps,
    )
    edge_advantage = edge.success and (not greedy.success or edge.minimum_norm < greedy.minimum_norm)
    failure = None if edge.success else "edge_ranked_no_crossing_within_budget"
    return EdgeComparison(
        model.hidden,
        bad_seed,
        bad_loss,
        decision.action,
        decision.reasons,
        total_budget,
        estimator_units,
        edge,
        greedy,
        edge_advantage,
        failure,
        edge_estimate,
    )
