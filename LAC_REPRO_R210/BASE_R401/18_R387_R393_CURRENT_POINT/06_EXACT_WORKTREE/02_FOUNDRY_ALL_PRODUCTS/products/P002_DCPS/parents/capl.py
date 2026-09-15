"""Constraint-Aware Portfolio Policy Learner (CAPL) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class PolicyMetrics:
    mean_return: float
    return_volatility: float
    certainty_equivalent: float
    average_turnover: float
    total_transaction_cost: float
    objective: float


@dataclass(frozen=True)
class ActionAudit:
    maximum_sum_error: float
    minimum_weight: float
    maximum_weight: float
    maximum_realized_turnover: float
    sum_violations: int
    lower_bound_violations: int
    upper_bound_violations: int
    turnover_violations: int


@dataclass(frozen=True)
class PortfolioPolicyResult:
    coefficients: tuple[tuple[float, ...], ...]
    training_metrics: PolicyMetrics
    validation_metrics: PolicyMetrics
    equal_weight_validation_metrics: PolicyMetrics
    validation_weights: tuple[tuple[float, ...], ...]
    validation_action_audit: ActionAudit
    validation_objective_improvement_vs_equal_weight: float
    generations: int
    candidates_evaluated: int
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _capped_simplex(raw: np.ndarray, cap: float) -> np.ndarray:
    # ``raw`` is already a strictly positive simplex point. Cap any excess and
    # redistribute it over the still-free coordinates. At least one coordinate
    # becomes fixed per pass, so this terminates in at most ``assets`` passes.
    weights = raw.copy()
    fixed = np.zeros(raw.size, dtype=bool)
    for _ in range(raw.size):
        over = (weights > cap) & ~fixed
        if not np.any(over):
            break
        excess = float(np.sum(weights[over] - cap))
        weights[over] = cap
        fixed |= over
        free = ~fixed
        if np.any(free):
            free_total = float(np.sum(weights[free]))
            if free_total > 0:
                weights[free] += excess * weights[free] / free_total
            else:
                weights[free] += excess / np.sum(free)
    # Only floating-point cleanup; the redistribution itself preserves the sum.
    weights /= weights.sum()
    return weights


def _policy_actions(features: np.ndarray, coefficients: np.ndarray, cap: float, turnover_limit: float) -> np.ndarray:
    n, _ = features.shape
    assets = coefficients.shape[1]
    augmented = np.column_stack((np.ones(n), features))
    scores = augmented @ coefficients
    scores -= np.max(scores, axis=1, keepdims=True)
    raw_targets = np.exp(np.clip(scores, -40, 40))
    raw_targets /= raw_targets.sum(axis=1, keepdims=True)
    weights = np.empty((n, assets), dtype=float)
    previous = np.full(assets, 1.0 / assets)
    for index in range(n):
        target = _capped_simplex(raw_targets[index], cap)
        turnover = float(np.sum(np.abs(target - previous)))
        if turnover > turnover_limit:
            target = previous + (turnover_limit / turnover) * (target - previous)
        weights[index] = target
        previous = target
    return weights


def _metrics(weights: np.ndarray, returns: np.ndarray, risk_aversion: float, transaction_cost: float) -> PolicyMetrics:
    initial = np.full(weights.shape[1], 1.0 / weights.shape[1])
    prior = np.vstack((initial, weights[:-1]))
    turnover = np.sum(np.abs(weights - prior), axis=1)
    gross = np.sum(weights * returns, axis=1)
    net = gross - transaction_cost * turnover
    mean = float(np.mean(net))
    variance = float(np.var(net, ddof=1)) if net.size > 1 else 0.0
    certainty_equivalent = mean - 0.5 * risk_aversion * variance
    return PolicyMetrics(
        mean_return=mean,
        return_volatility=float(np.sqrt(variance)),
        certainty_equivalent=float(certainty_equivalent),
        average_turnover=float(np.mean(turnover)),
        total_transaction_cost=float(transaction_cost * np.sum(turnover)),
        objective=float(-certainty_equivalent),
    )


def _audit(weights: np.ndarray, cap: float, turnover_limit: float) -> ActionAudit:
    initial = np.full(weights.shape[1], 1.0 / weights.shape[1])
    prior = np.vstack((initial, weights[:-1]))
    turnover = np.sum(np.abs(weights - prior), axis=1)
    tolerance = 1e-10
    return ActionAudit(
        maximum_sum_error=float(np.max(np.abs(weights.sum(axis=1) - 1.0))),
        minimum_weight=float(np.min(weights)),
        maximum_weight=float(np.max(weights)),
        maximum_realized_turnover=float(np.max(turnover)),
        sum_violations=int(np.sum(np.abs(weights.sum(axis=1) - 1.0) > tolerance)),
        lower_bound_violations=int(np.sum(weights < -tolerance)),
        upper_bound_violations=int(np.sum(weights > cap + tolerance)),
        turnover_violations=int(np.sum(turnover > turnover_limit + tolerance)),
    )


def learn_portfolio_policy(
    training_features: Sequence[Sequence[float]],
    training_asset_returns: Sequence[Sequence[float]],
    validation_features: Sequence[Sequence[float]],
    validation_asset_returns: Sequence[Sequence[float]],
    *,
    maximum_asset_weight: float,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
    population_size: int = 80,
    generations: int = 30,
    elite_fraction: float = 0.15,
    seed: int = 0,
) -> PortfolioPolicyResult:
    """Learn a linear-softmax policy by direct constrained action performance."""

    x_train = np.asarray(training_features, dtype=float)
    r_train = np.asarray(training_asset_returns, dtype=float)
    x_val = np.asarray(validation_features, dtype=float)
    r_val = np.asarray(validation_asset_returns, dtype=float)
    if any(value.ndim != 2 for value in (x_train, r_train, x_val, r_val)):
        raise ValueError("features and returns must be matrices")
    if x_train.shape[0] != r_train.shape[0] or x_val.shape[0] != r_val.shape[0]:
        raise ValueError("feature and return rows must match")
    if x_train.shape[1] != x_val.shape[1] or r_train.shape[1] != r_val.shape[1] or r_train.shape[1] < 2:
        raise ValueError("training and validation dimensions must match")
    if min(x_train.shape[0], x_val.shape[0]) < 5 or not all(np.all(np.isfinite(v)) for v in (x_train, r_train, x_val, r_val)):
        raise ValueError("finite training and validation samples of length >= 5 are required")
    assets = r_train.shape[1]
    if maximum_asset_weight < 1.0 / assets or maximum_asset_weight > 1.0:
        raise ValueError("maximum_asset_weight must permit a fully invested portfolio")
    if maximum_turnover <= 0 or maximum_turnover > 2 or risk_aversion < 0 or transaction_cost < 0:
        raise ValueError("turnover must be in (0,2] and cost/risk aversion nonnegative")
    if population_size < 10 or generations < 1 or not 0 < elite_fraction <= .5:
        raise ValueError("evolution settings are invalid")

    dimension = (x_train.shape[1] + 1) * assets
    rng = np.random.default_rng(seed)
    mean = np.zeros(dimension)
    scale = np.ones(dimension)
    elite_count = max(2, int(round(population_size * elite_fraction)))
    best_vector = mean.copy()
    best_metrics = _metrics(
        _policy_actions(x_train, best_vector.reshape(x_train.shape[1] + 1, assets), maximum_asset_weight, maximum_turnover),
        r_train, risk_aversion, transaction_cost,
    )
    evaluated = 1
    for _ in range(generations):
        population = mean + rng.normal(size=(population_size, dimension)) * scale
        population[0] = best_vector
        scored: list[tuple[float, int, PolicyMetrics]] = []
        for index, vector in enumerate(population):
            coefficients = vector.reshape(x_train.shape[1] + 1, assets)
            weights = _policy_actions(x_train, coefficients, maximum_asset_weight, maximum_turnover)
            metrics = _metrics(weights, r_train, risk_aversion, transaction_cost)
            scored.append((metrics.objective, index, metrics))
        scored.sort(key=lambda item: (item[0], item[1]))
        elite = population[[item[1] for item in scored[:elite_count]]]
        mean = .25 * mean + .75 * elite.mean(axis=0)
        scale = np.maximum(.03, .25 * scale + .75 * (elite.std(axis=0) + .02))
        if scored[0][0] < best_metrics.objective:
            best_metrics = scored[0][2]
            best_vector = population[scored[0][1]].copy()
        evaluated += population_size

    coefficients = best_vector.reshape(x_train.shape[1] + 1, assets)
    training_weights = _policy_actions(x_train, coefficients, maximum_asset_weight, maximum_turnover)
    validation_weights = _policy_actions(x_val, coefficients, maximum_asset_weight, maximum_turnover)
    training_metrics = _metrics(training_weights, r_train, risk_aversion, transaction_cost)
    validation_metrics = _metrics(validation_weights, r_val, risk_aversion, transaction_cost)
    equal_weights = np.full_like(validation_weights, 1.0 / assets)
    equal_metrics = _metrics(equal_weights, r_val, risk_aversion, transaction_cost)
    audit = _audit(validation_weights, maximum_asset_weight, maximum_turnover)
    violations = audit.sum_violations + audit.lower_bound_violations + audit.upper_bound_violations + audit.turnover_violations
    return PortfolioPolicyResult(
        coefficients=tuple(tuple(map(float, row)) for row in coefficients),
        training_metrics=training_metrics,
        validation_metrics=validation_metrics,
        equal_weight_validation_metrics=equal_metrics,
        validation_weights=tuple(tuple(map(float, row)) for row in validation_weights),
        validation_action_audit=audit,
        validation_objective_improvement_vs_equal_weight=float(equal_metrics.objective - validation_metrics.objective),
        generations=generations,
        candidates_evaluated=evaluated,
        status="CONSTRAINT_CERTIFIED_POLICY_LEARNED" if violations == 0 else "POLICY_RETURNED_WITH_ACTION_VIOLATIONS",
    )
