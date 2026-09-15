"""SWCAPL: target-support-weighted CAPL policy learning.

Composition: P090 SWDL -> R041 CAPL.

P090's documented mechanism supplies externally justified target importance
weights plus an overlap/ESS support gate.  SWCAPL places those weights *inside*
CAPL's direct realized-action objective before the evolutionary policy search.
The mechanism-removal control uses the same samples, CAPL action constraints,
optimizer settings, and seed with uniform observation weights.

Claim boundary: importance weights are caller-supplied and must be externally
justified.  A usable ESS is only a support diagnostic; it does not establish
transportability or causal identification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Sequence

import numpy as np

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
CAPL_PATH = PACKAGE_ROOT / "02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R041_CONSTRAINED_POLICY_CAPL/capl.py"
OWS_PATH = PACKAGE_ROOT / "02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS/IM274_IM290_OWS/ows.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_capl = _load("swcapl_parent_capl", CAPL_PATH)
_ows = _load("swcapl_parent_ows", OWS_PATH)


@dataclass(frozen=True)
class WeightedPolicyMetrics:
    weighted_mean_return: float
    weighted_return_volatility: float
    weighted_certainty_equivalent: float
    weighted_average_turnover: float
    weighted_objective: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SWCAPLResult:
    support_status: str
    effective_sample_size: float
    effective_sample_fraction: float
    max_normalized_weight: float
    candidate_training_metrics: WeightedPolicyMetrics
    control_training_metrics: WeightedPolicyMetrics
    candidate_target_validation_objective: float
    control_target_validation_objective: float
    target_validation_gain_vs_removed_mechanism: float
    candidate_validation_weights: tuple[tuple[float, ...], ...]
    control_validation_weights: tuple[tuple[float, ...], ...]
    candidate_action_audit: dict
    control_action_audit: dict
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _validated_sample_weights(weights: Sequence[float], n: int) -> np.ndarray:
    w = np.asarray(weights, dtype=float)
    if w.shape != (n,) or np.any(~np.isfinite(w)) or np.any(w < 0):
        raise ValueError("importance weights must be a finite nonnegative vector matching training rows")
    if float(np.sum(w)) <= 0:
        raise ValueError("importance weights must have positive total")
    return w


def _weighted_metrics(
    policy_weights: np.ndarray,
    returns: np.ndarray,
    observation_weights: np.ndarray,
    risk_aversion: float,
    transaction_cost: float,
) -> WeightedPolicyMetrics:
    p = np.asarray(observation_weights, dtype=float)
    p = p / float(np.sum(p))
    initial = np.full(policy_weights.shape[1], 1.0 / policy_weights.shape[1])
    prior = np.vstack((initial, policy_weights[:-1]))
    turnover = np.sum(np.abs(policy_weights - prior), axis=1)
    gross = np.sum(policy_weights * returns, axis=1)
    net = gross - transaction_cost * turnover
    mean = float(p @ net)
    variance = float(p @ ((net - mean) ** 2))
    certainty_equivalent = mean - 0.5 * risk_aversion * variance
    return WeightedPolicyMetrics(
        weighted_mean_return=mean,
        weighted_return_volatility=float(np.sqrt(max(0.0, variance))),
        weighted_certainty_equivalent=float(certainty_equivalent),
        weighted_average_turnover=float(p @ turnover),
        weighted_objective=float(-certainty_equivalent),
    )


def _learn_weighted_policy(
    features: np.ndarray,
    returns: np.ndarray,
    observation_weights: np.ndarray,
    *,
    maximum_asset_weight: float,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
    population_size: int,
    generations: int,
    elite_fraction: float,
    seed: int,
):
    n, feature_count = features.shape
    assets = returns.shape[1]
    dimension = (feature_count + 1) * assets
    rng = np.random.default_rng(seed)
    mean = np.zeros(dimension)
    scale = np.ones(dimension)
    elite_count = max(2, int(round(population_size * elite_fraction)))
    best_vector = mean.copy()

    def evaluate(vector: np.ndarray):
        coefficients = vector.reshape(feature_count + 1, assets)
        actions = _capl._policy_actions(features, coefficients, maximum_asset_weight, maximum_turnover)
        return _weighted_metrics(actions, returns, observation_weights, risk_aversion, transaction_cost)

    best_metrics = evaluate(best_vector)
    for _ in range(generations):
        population = mean + rng.normal(size=(population_size, dimension)) * scale
        population[0] = best_vector
        scored = []
        for index, vector in enumerate(population):
            metrics = evaluate(vector)
            scored.append((metrics.weighted_objective, index, metrics))
        scored.sort(key=lambda item: (item[0], item[1]))
        elite = population[[item[1] for item in scored[:elite_count]]]
        mean = 0.25 * mean + 0.75 * elite.mean(axis=0)
        scale = np.maximum(0.03, 0.25 * scale + 0.75 * (elite.std(axis=0) + 0.02))
        if scored[0][0] < best_metrics.weighted_objective:
            best_metrics = scored[0][2]
            best_vector = population[scored[0][1]].copy()
    return best_vector.reshape(feature_count + 1, assets), best_metrics


def learn_support_weighted_policy(
    training_features: Sequence[Sequence[float]],
    training_asset_returns: Sequence[Sequence[float]],
    target_validation_features: Sequence[Sequence[float]],
    target_validation_asset_returns: Sequence[Sequence[float]],
    *,
    target_importance_weights: Sequence[float],
    fragile_ess_fraction: float,
    maximum_asset_weight: float,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
    population_size: int = 50,
    generations: int = 15,
    elite_fraction: float = 0.20,
    seed: int = 0,
) -> SWCAPLResult:
    """Learn CAPL under an externally justified target-weighted training objective.

    The target validation sample is kept as a common, unweighted reference for
    candidate-vs-control comparison.  Importance weights affect training only.
    """
    x_train = np.asarray(training_features, dtype=float)
    r_train = np.asarray(training_asset_returns, dtype=float)
    x_val = np.asarray(target_validation_features, dtype=float)
    r_val = np.asarray(target_validation_asset_returns, dtype=float)
    if any(v.ndim != 2 for v in (x_train, r_train, x_val, r_val)):
        raise ValueError("features and returns must be matrices")
    if x_train.shape[0] != r_train.shape[0] or x_val.shape[0] != r_val.shape[0]:
        raise ValueError("feature and return rows must align")
    if x_train.shape[1] != x_val.shape[1] or r_train.shape[1] != r_val.shape[1] or r_train.shape[1] < 2:
        raise ValueError("training and validation dimensions must align")
    if min(len(x_train), len(x_val)) < 5 or not all(np.all(np.isfinite(v)) for v in (x_train, r_train, x_val, r_val)):
        raise ValueError("finite training and validation samples of length >=5 are required")
    assets = r_train.shape[1]
    if maximum_asset_weight < 1.0 / assets or maximum_asset_weight > 1.0:
        raise ValueError("maximum_asset_weight must admit a fully invested portfolio")
    if maximum_turnover <= 0 or maximum_turnover > 2 or risk_aversion < 0 or transaction_cost < 0:
        raise ValueError("invalid turnover/risk/cost configuration")
    if population_size < 10 or generations < 1 or not 0 < elite_fraction <= 0.5:
        raise ValueError("invalid evolution settings")

    iw = _validated_sample_weights(target_importance_weights, len(x_train))
    audit = _ows.OverlapAwareWeightStabilizer(fragile_ess_fraction=float(fragile_ess_fraction)).audit(iw)
    if audit.status != "SUPPORT_USABLE":
        raise ValueError(
            f"target importance weights fail the declared overlap/ESS gate: ESS fraction={audit.effective_sample_fraction:.6g}"
        )

    candidate_coef, candidate_train = _learn_weighted_policy(
        x_train, r_train, iw,
        maximum_asset_weight=maximum_asset_weight, maximum_turnover=maximum_turnover,
        risk_aversion=risk_aversion, transaction_cost=transaction_cost,
        population_size=population_size, generations=generations,
        elite_fraction=elite_fraction, seed=seed,
    )
    uniform = np.ones(len(x_train), dtype=float)
    control_coef, control_train = _learn_weighted_policy(
        x_train, r_train, uniform,
        maximum_asset_weight=maximum_asset_weight, maximum_turnover=maximum_turnover,
        risk_aversion=risk_aversion, transaction_cost=transaction_cost,
        population_size=population_size, generations=generations,
        elite_fraction=elite_fraction, seed=seed,
    )

    candidate_actions = _capl._policy_actions(x_val, candidate_coef, maximum_asset_weight, maximum_turnover)
    control_actions = _capl._policy_actions(x_val, control_coef, maximum_asset_weight, maximum_turnover)
    candidate_val = _capl._metrics(candidate_actions, r_val, risk_aversion, transaction_cost)
    control_val = _capl._metrics(control_actions, r_val, risk_aversion, transaction_cost)
    candidate_audit = _capl._audit(candidate_actions, maximum_asset_weight, maximum_turnover)
    control_audit = _capl._audit(control_actions, maximum_asset_weight, maximum_turnover)
    violations = sum(
        a.sum_violations + a.lower_bound_violations + a.upper_bound_violations + a.turnover_violations
        for a in (candidate_audit, control_audit)
    )
    equal_weights = bool(np.allclose(iw / np.mean(iw), np.ones_like(iw), atol=0, rtol=0))
    if equal_weights and tuple(map(tuple, candidate_actions)) != tuple(map(tuple, control_actions)):
        raise RuntimeError("uniform importance weights must collapse exactly to the CAPL control")
    status = "TARGET_WEIGHTED_POLICY_LEARNED" if violations == 0 and not equal_weights else (
        "TARGET_WEIGHTING_COLLAPSED_TO_CAPL_CONTROL" if violations == 0 else "ACTION_CONSTRAINT_VIOLATION"
    )
    return SWCAPLResult(
        support_status=audit.status,
        effective_sample_size=float(audit.effective_sample_size),
        effective_sample_fraction=float(audit.effective_sample_fraction),
        max_normalized_weight=float(audit.max_normalized_weight),
        candidate_training_metrics=candidate_train,
        control_training_metrics=control_train,
        candidate_target_validation_objective=float(candidate_val.objective),
        control_target_validation_objective=float(control_val.objective),
        target_validation_gain_vs_removed_mechanism=float(control_val.objective - candidate_val.objective),
        candidate_validation_weights=tuple(tuple(map(float, row)) for row in candidate_actions),
        control_validation_weights=tuple(tuple(map(float, row)) for row in control_actions),
        candidate_action_audit=candidate_audit.to_dict() if hasattr(candidate_audit, 'to_dict') else asdict(candidate_audit),
        control_action_audit=control_audit.to_dict() if hasattr(control_audit, 'to_dict') else asdict(control_audit),
        status=status,
    )
