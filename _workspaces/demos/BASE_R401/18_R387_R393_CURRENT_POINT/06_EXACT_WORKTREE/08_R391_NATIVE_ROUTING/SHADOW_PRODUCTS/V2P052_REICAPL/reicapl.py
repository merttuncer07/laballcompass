"""REICAPL: REIS-driven heterogeneous feasible caps for CAPL-style policy learning.

Mechanism: P028 REIS consequence-aware safeguard selection changes the feasible
portfolio action set *before* policy optimization by tightening the cap of the
asset explicitly aligned to each selected evidence record.  The mechanism-
removal control uses the same optimizer/data/random seed with uniform base caps.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import importlib.util
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
REIS_PATH = PACKAGE_ROOT / "02_FOUNDRY_ALL_PRODUCTS/products/P028_REIS/reis.py"
CAPL_PATH = PACKAGE_ROOT / "02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R041_CONSTRAINED_POLICY_CAPL/capl.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_reis = _load("reicapl_parent_reis", REIS_PATH)
_capl = _load("reicapl_parent_capl", CAPL_PATH)


@dataclass(frozen=True)
class HeterogeneousCapAudit:
    maximum_sum_error: float
    minimum_weight: float
    maximum_cap_excess: float
    maximum_realized_turnover: float
    sum_violations: int
    lower_bound_violations: int
    cap_violations: int
    turnover_violations: int


@dataclass(frozen=True)
class REICAPLResult:
    selected_safeguards: tuple[str, ...]
    posterior_only_safeguards: tuple[str, ...]
    selected_assets: tuple[str, ...]
    candidate_asset_caps: tuple[float, ...]
    control_asset_caps: tuple[float, ...]
    posterior_only_asset_caps: tuple[float, ...]
    candidate_validation_objective: float
    control_validation_objective: float
    posterior_only_validation_objective: float
    gain_vs_removed_mechanism: float
    gain_vs_posterior_only: float
    candidate_average_turnover: float
    control_average_turnover: float
    candidate_validation_weights: tuple[tuple[float, ...], ...]
    control_validation_weights: tuple[tuple[float, ...], ...]
    candidate_audit: HeterogeneousCapAudit
    control_audit: HeterogeneousCapAudit
    posterior_only_audit: HeterogeneousCapAudit
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_caps(caps: np.ndarray, assets: int) -> None:
    if caps.shape != (assets,) or not np.all(np.isfinite(caps)):
        raise ValueError("asset caps must be a finite vector matching asset count")
    # This v0.1 preserves CAPL's equal-weight initial state exactly.
    if np.any(caps < 1.0 / assets - 1e-12) or np.any(caps > 1.0 + 1e-12):
        raise ValueError("every cap must admit CAPL's equal-weight initial state and be <= 1")
    if float(np.sum(caps)) < 1.0 - 1e-12:
        raise ValueError("asset caps do not admit a fully invested portfolio")


def _heterogeneous_capped_simplex(raw: np.ndarray, caps: np.ndarray) -> np.ndarray:
    raw = np.asarray(raw, dtype=float)
    caps = np.asarray(caps, dtype=float)
    if raw.ndim != 1 or raw.shape != caps.shape or np.any(raw < 0) or not np.all(np.isfinite(raw)):
        raise ValueError("raw action and caps must be aligned finite nonnegative vectors")
    if float(np.sum(raw)) <= 0:
        raise ValueError("raw action must have positive mass")
    _validate_caps(caps, raw.size)
    weights = raw / float(np.sum(raw))
    fixed = np.zeros(raw.size, dtype=bool)
    for _ in range(raw.size + 1):
        over = (weights > caps + 1e-15) & ~fixed
        if not np.any(over):
            break
        excess = float(np.sum(weights[over] - caps[over]))
        weights[over] = caps[over]
        fixed |= over
        free = ~fixed
        if not np.any(free):
            break
        free_total = float(np.sum(weights[free]))
        if free_total > 0:
            weights[free] += excess * weights[free] / free_total
        else:
            weights[free] += excess / int(np.sum(free))
    weights /= float(np.sum(weights))
    if np.max(weights - caps) > 1e-10:
        raise RuntimeError("heterogeneous cap projection failed")
    return weights


def _policy_actions(features: np.ndarray, coefficients: np.ndarray, caps: np.ndarray, turnover_limit: float) -> np.ndarray:
    n, _ = features.shape
    assets = coefficients.shape[1]
    _validate_caps(caps, assets)
    augmented = np.column_stack((np.ones(n), features))
    scores = augmented @ coefficients
    scores -= np.max(scores, axis=1, keepdims=True)
    raw_targets = np.exp(np.clip(scores, -40, 40))
    raw_targets /= raw_targets.sum(axis=1, keepdims=True)
    weights = np.empty((n, assets), dtype=float)
    previous = np.full(assets, 1.0 / assets)
    for index in range(n):
        target = _heterogeneous_capped_simplex(raw_targets[index], caps)
        turnover = float(np.sum(np.abs(target - previous)))
        if turnover > turnover_limit:
            target = previous + (turnover_limit / turnover) * (target - previous)
        weights[index] = target
        previous = target
    return weights


def _audit(weights: np.ndarray, caps: np.ndarray, turnover_limit: float) -> HeterogeneousCapAudit:
    initial = np.full(weights.shape[1], 1.0 / weights.shape[1])
    prior = np.vstack((initial, weights[:-1]))
    turnover = np.sum(np.abs(weights - prior), axis=1)
    excess = weights - caps[None, :]
    tol = 1e-10
    return HeterogeneousCapAudit(
        maximum_sum_error=float(np.max(np.abs(weights.sum(axis=1) - 1.0))),
        minimum_weight=float(np.min(weights)),
        maximum_cap_excess=float(max(0.0, np.max(excess))),
        maximum_realized_turnover=float(np.max(turnover)),
        sum_violations=int(np.sum(np.abs(weights.sum(axis=1) - 1.0) > tol)),
        lower_bound_violations=int(np.sum(weights < -tol)),
        cap_violations=int(np.sum(excess > tol)),
        turnover_violations=int(np.sum(turnover > turnover_limit + tol)),
    )


def _learn_with_caps(
    training_features: np.ndarray,
    training_returns: np.ndarray,
    validation_features: np.ndarray,
    validation_returns: np.ndarray,
    caps: np.ndarray,
    *,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
    population_size: int,
    generations: int,
    elite_fraction: float,
    seed: int,
):
    x_train = np.asarray(training_features, dtype=float)
    r_train = np.asarray(training_returns, dtype=float)
    x_val = np.asarray(validation_features, dtype=float)
    r_val = np.asarray(validation_returns, dtype=float)
    if any(v.ndim != 2 for v in (x_train, r_train, x_val, r_val)):
        raise ValueError("features and returns must be matrices")
    if x_train.shape[0] != r_train.shape[0] or x_val.shape[0] != r_val.shape[0]:
        raise ValueError("feature and return rows must align")
    if x_train.shape[1] != x_val.shape[1] or r_train.shape[1] != r_val.shape[1] or r_train.shape[1] < 2:
        raise ValueError("training and validation dimensions must align")
    if min(x_train.shape[0], x_val.shape[0]) < 5 or not all(np.all(np.isfinite(v)) for v in (x_train, r_train, x_val, r_val)):
        raise ValueError("finite training/validation samples of length >=5 are required")
    assets = r_train.shape[1]
    _validate_caps(caps, assets)
    if maximum_turnover <= 0 or maximum_turnover > 2 or risk_aversion < 0 or transaction_cost < 0:
        raise ValueError("invalid turnover/risk/cost configuration")
    if population_size < 10 or generations < 1 or not 0 < elite_fraction <= 0.5:
        raise ValueError("invalid evolution settings")

    dimension = (x_train.shape[1] + 1) * assets
    rng = np.random.default_rng(seed)
    mean = np.zeros(dimension)
    scale = np.ones(dimension)
    elite_count = max(2, int(round(population_size * elite_fraction)))
    best_vector = mean.copy()
    best_metrics = _capl._metrics(
        _policy_actions(x_train, best_vector.reshape(x_train.shape[1] + 1, assets), caps, maximum_turnover),
        r_train, risk_aversion, transaction_cost,
    )
    for _ in range(generations):
        population = mean + rng.normal(size=(population_size, dimension)) * scale
        population[0] = best_vector
        scored = []
        for index, vector in enumerate(population):
            coefficients = vector.reshape(x_train.shape[1] + 1, assets)
            metrics = _capl._metrics(
                _policy_actions(x_train, coefficients, caps, maximum_turnover),
                r_train, risk_aversion, transaction_cost,
            )
            scored.append((metrics.objective, index, metrics))
        scored.sort(key=lambda item: (item[0], item[1]))
        elite = population[[item[1] for item in scored[:elite_count]]]
        mean = 0.25 * mean + 0.75 * elite.mean(axis=0)
        scale = np.maximum(0.03, 0.25 * scale + 0.75 * (elite.std(axis=0) + 0.02))
        if scored[0][0] < best_metrics.objective:
            best_metrics = scored[0][2]
            best_vector = population[scored[0][1]].copy()

    coefficients = best_vector.reshape(x_train.shape[1] + 1, assets)
    validation_weights = _policy_actions(x_val, coefficients, caps, maximum_turnover)
    validation_metrics = _capl._metrics(validation_weights, r_val, risk_aversion, transaction_cost)
    audit = _audit(validation_weights, caps, maximum_turnover)
    return validation_metrics, validation_weights, audit


def _posterior_only_safeguards(posterior: Mapping[str, float], costs: Mapping[str, float], budget: float) -> tuple[str, ...]:
    keys = set(posterior)
    if keys != set(costs):
        raise ValueError("posterior and cost records must align")
    ordered = sorted(keys)
    feasible = []
    for n in range(len(ordered) + 1):
        for subset in combinations(ordered, n):
            cost = sum(float(costs[k]) for k in subset)
            if cost <= budget + 1e-12:
                feasible.append((sum(float(posterior[k]) for k in subset), subset))
    return max(feasible, key=lambda x: (x[0], tuple(reversed(x[1]))))[1]


def _caps_from_safeguards(
    safeguards: Sequence[str], record_to_asset: Mapping[str, str], asset_names: Sequence[str],
    *, base_cap: float, protected_cap: float,
) -> np.ndarray:
    names = tuple(map(str, asset_names))
    if len(set(names)) != len(names):
        raise ValueError("asset names must be unique")
    if set(record_to_asset) != set(record_to_asset.keys()):
        raise ValueError("invalid record mapping")
    lookup = {name: i for i, name in enumerate(names)}
    caps = np.full(len(names), float(base_cap))
    for record in safeguards:
        if record not in record_to_asset:
            raise ValueError(f"selected record lacks explicit record-to-asset alignment: {record}")
        asset = str(record_to_asset[record])
        if asset not in lookup:
            raise ValueError(f"record {record} maps to unknown asset {asset}")
        caps[lookup[asset]] = min(caps[lookup[asset]], float(protected_cap))
    _validate_caps(caps, len(names))
    return caps


def learn_relational_evidence_constrained_policy(
    training_features: Sequence[Sequence[float]],
    training_asset_returns: Sequence[Sequence[float]],
    validation_features: Sequence[Sequence[float]],
    validation_asset_returns: Sequence[Sequence[float]],
    *,
    posterior_culprit: Mapping[str, float],
    empirical_consequence: Mapping[str, float],
    safeguard_cost: Mapping[str, float],
    record_to_asset: Mapping[str, str],
    asset_names: Sequence[str],
    safeguard_budget: float,
    base_asset_cap: float,
    protected_asset_cap: float,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
    population_size: int = 30,
    generations: int = 8,
    elite_fraction: float = 0.15,
    seed: int = 0,
) -> REICAPLResult:
    """Couple REIS safeguard allocation into CAPL-style heterogeneous feasible caps.

    Evidence boundary: this function assumes an explicit semantic record→asset
    alignment supplied by the caller.  It does not infer that mapping from data.
    """
    x_train = np.asarray(training_features, dtype=float)
    r_train = np.asarray(training_asset_returns, dtype=float)
    x_val = np.asarray(validation_features, dtype=float)
    r_val = np.asarray(validation_asset_returns, dtype=float)
    if safeguard_budget < 0:
        raise ValueError("safeguard budget must be nonnegative")
    if protected_asset_cap > base_asset_cap:
        raise ValueError("protected cap must not exceed base cap")
    if r_train.ndim != 2 or len(asset_names) != r_train.shape[1]:
        raise ValueError("asset_names must match return columns")
    records = set(posterior_culprit)
    if records != set(empirical_consequence) or records != set(safeguard_cost):
        raise ValueError("REIS record sets must align")
    if records != set(record_to_asset):
        raise ValueError("every REIS record requires an explicit record-to-asset alignment")

    reis_result = _reis.allocate_relational_safeguards(
        dict(posterior_culprit), dict(empirical_consequence), dict(safeguard_cost), budget=float(safeguard_budget)
    )
    posterior_only = _posterior_only_safeguards(posterior_culprit, safeguard_cost, float(safeguard_budget))
    candidate_caps = _caps_from_safeguards(
        reis_result.selected_safeguards, record_to_asset, asset_names,
        base_cap=base_asset_cap, protected_cap=protected_asset_cap,
    )
    posterior_caps = _caps_from_safeguards(
        posterior_only, record_to_asset, asset_names,
        base_cap=base_asset_cap, protected_cap=protected_asset_cap,
    )
    control_caps = np.full(len(asset_names), float(base_asset_cap))
    _validate_caps(control_caps, len(asset_names))

    common = dict(
        maximum_turnover=float(maximum_turnover), risk_aversion=float(risk_aversion),
        transaction_cost=float(transaction_cost), population_size=int(population_size),
        generations=int(generations), elite_fraction=float(elite_fraction), seed=int(seed),
    )
    candidate_metrics, candidate_weights, candidate_audit = _learn_with_caps(
        x_train, r_train, x_val, r_val, candidate_caps, **common
    )
    control_metrics, control_weights, control_audit = _learn_with_caps(
        x_train, r_train, x_val, r_val, control_caps, **common
    )
    posterior_metrics, _, posterior_audit = _learn_with_caps(
        x_train, r_train, x_val, r_val, posterior_caps, **common
    )
    selected_assets = tuple(sorted({str(record_to_asset[r]) for r in reis_result.selected_safeguards}))
    audits = (candidate_audit, control_audit, posterior_audit)
    violations = sum(
        a.sum_violations + a.lower_bound_violations + a.cap_violations + a.turnover_violations
        for a in audits
    )
    return REICAPLResult(
        selected_safeguards=tuple(reis_result.selected_safeguards),
        posterior_only_safeguards=tuple(posterior_only),
        selected_assets=selected_assets,
        candidate_asset_caps=tuple(map(float, candidate_caps)),
        control_asset_caps=tuple(map(float, control_caps)),
        posterior_only_asset_caps=tuple(map(float, posterior_caps)),
        candidate_validation_objective=float(candidate_metrics.objective),
        control_validation_objective=float(control_metrics.objective),
        posterior_only_validation_objective=float(posterior_metrics.objective),
        gain_vs_removed_mechanism=float(control_metrics.objective - candidate_metrics.objective),
        gain_vs_posterior_only=float(posterior_metrics.objective - candidate_metrics.objective),
        candidate_average_turnover=float(candidate_metrics.average_turnover),
        control_average_turnover=float(control_metrics.average_turnover),
        candidate_validation_weights=tuple(tuple(map(float, row)) for row in candidate_weights),
        control_validation_weights=tuple(tuple(map(float, row)) for row in control_weights),
        candidate_audit=candidate_audit,
        control_audit=control_audit,
        posterior_only_audit=posterior_audit,
        status="REIS_CHANGED_CAPL_FEASIBLE_SET" if tuple(candidate_caps) != tuple(control_caps) and violations == 0 else (
            "REIS_COLLAPSED_TO_CONTROL" if tuple(candidate_caps) == tuple(control_caps) and violations == 0 else "ACTION_CONSTRAINT_VIOLATION"
        ),
    )
