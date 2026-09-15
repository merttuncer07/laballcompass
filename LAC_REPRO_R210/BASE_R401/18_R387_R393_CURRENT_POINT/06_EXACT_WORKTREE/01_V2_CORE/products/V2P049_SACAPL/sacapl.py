"""Support-Aware Covariance Portfolio Policy Learner (SACAPL) shadow candidate.

Composition: R037 SACPS -> R041 CAPL.
SACPS changes the risk geometry used to score CAPL's constrained policy actions.
The mechanism-removing control uses the same policy architecture, constraints,
optimizer, seed, returns, and transaction costs but substitutes the unstructured
raw sample covariance for the support-aware covariance.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class CovariancePolicyMetrics:
    mean_net_return: float
    predicted_variance: float
    covariance_certainty_equivalent: float
    average_turnover: float
    objective: float

    def to_dict(self) -> dict:
        return asdict(self)


def _covariance_policy_metrics(
    policy_actions,
    features: np.ndarray,
    returns: np.ndarray,
    coefficients: np.ndarray,
    covariance: np.ndarray,
    *,
    maximum_asset_weight: float,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
) -> tuple[CovariancePolicyMetrics, np.ndarray]:
    weights = policy_actions(features, coefficients, maximum_asset_weight, maximum_turnover)
    initial = np.full(weights.shape[1], 1.0 / weights.shape[1])
    prior = np.vstack((initial, weights[:-1]))
    turnover = np.sum(np.abs(weights - prior), axis=1)
    gross = np.sum(weights * returns, axis=1)
    net = gross - transaction_cost * turnover
    predicted_variance = np.einsum("ti,ij,tj->t", weights, covariance, weights)
    mean_net = float(np.mean(net))
    mean_predicted_variance = float(np.mean(predicted_variance))
    certainty_equivalent = mean_net - 0.5 * risk_aversion * mean_predicted_variance
    return (
        CovariancePolicyMetrics(
            mean_net_return=mean_net,
            predicted_variance=mean_predicted_variance,
            covariance_certainty_equivalent=float(certainty_equivalent),
            average_turnover=float(np.mean(turnover)),
            objective=float(-certainty_equivalent),
        ),
        weights,
    )


def _learn_with_covariance_geometry(
    policy_actions,
    training_features: np.ndarray,
    training_returns: np.ndarray,
    covariance: np.ndarray,
    *,
    maximum_asset_weight: float,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
    population_size: int,
    generations: int,
    elite_fraction: float,
    seed: int,
) -> tuple[np.ndarray, CovariancePolicyMetrics, int]:
    """CAPL-style direct policy search with an explicit covariance risk term."""
    assets = training_returns.shape[1]
    dimension = (training_features.shape[1] + 1) * assets
    rng = np.random.default_rng(seed)
    mean = np.zeros(dimension)
    scale = np.ones(dimension)
    elite_count = max(2, int(round(population_size * elite_fraction)))
    best_vector = mean.copy()
    best_metrics, _ = _covariance_policy_metrics(
        policy_actions,
        training_features,
        training_returns,
        best_vector.reshape(training_features.shape[1] + 1, assets),
        covariance,
        maximum_asset_weight=maximum_asset_weight,
        maximum_turnover=maximum_turnover,
        risk_aversion=risk_aversion,
        transaction_cost=transaction_cost,
    )
    evaluated = 1
    for _ in range(generations):
        population = mean + rng.normal(size=(population_size, dimension)) * scale
        population[0] = best_vector
        scored: list[tuple[float, int, CovariancePolicyMetrics]] = []
        for index, vector in enumerate(population):
            metrics, _ = _covariance_policy_metrics(
                policy_actions,
                training_features,
                training_returns,
                vector.reshape(training_features.shape[1] + 1, assets),
                covariance,
                maximum_asset_weight=maximum_asset_weight,
                maximum_turnover=maximum_turnover,
                risk_aversion=risk_aversion,
                transaction_cost=transaction_cost,
            )
            scored.append((metrics.objective, index, metrics))
        scored.sort(key=lambda item: (item[0], item[1]))
        elite = population[[item[1] for item in scored[:elite_count]]]
        mean = 0.25 * mean + 0.75 * elite.mean(axis=0)
        scale = np.maximum(0.03, 0.25 * scale + 0.75 * (elite.std(axis=0) + 0.02))
        if scored[0][0] < best_metrics.objective:
            best_metrics = scored[0][2]
            best_vector = population[scored[0][1]].copy()
        evaluated += population_size
    final_coefficients = best_vector.reshape(training_features.shape[1] + 1, assets)
    final_metrics, _ = _covariance_policy_metrics(
        policy_actions,
        training_features,
        training_returns,
        final_coefficients,
        covariance,
        maximum_asset_weight=maximum_asset_weight,
        maximum_turnover=maximum_turnover,
        risk_aversion=risk_aversion,
        transaction_cost=transaction_cost,
    )
    return final_coefficients, final_metrics, evaluated


def support_covariance_aware_policy(
    capl_module,
    covariance_estimator,
    training_features: Sequence[Sequence[float]],
    training_asset_returns: Sequence[Sequence[float]],
    validation_features: Sequence[Sequence[float]],
    validation_asset_returns: Sequence[Sequence[float]],
    risk_training_returns: Sequence[Sequence[float]],
    support_mask: Sequence[Sequence[bool]],
    *,
    risk_calibration_returns: Sequence[Sequence[float]] | None = None,
    maximum_calibration_off_support_correlation: float | None = None,
    shrinkage_grid: Sequence[float] = tuple(np.linspace(0.0, 1.0, 21)),
    maximum_asset_weight: float,
    maximum_turnover: float,
    risk_aversion: float,
    transaction_cost: float,
    population_size: int = 40,
    generations: int = 12,
    elite_fraction: float = 0.15,
    seed: int = 0,
) -> dict:
    """Learn CAPL policies under support-aware versus raw covariance geometry.

    The candidate and removal control share the same CAPL action map, constraints,
    population-search settings, seed, training returns, and validation data. Only
    the covariance matrix inside the risk term is changed.
    """
    x_train = np.asarray(training_features, dtype=float)
    r_train = np.asarray(training_asset_returns, dtype=float)
    x_val = np.asarray(validation_features, dtype=float)
    r_val = np.asarray(validation_asset_returns, dtype=float)
    risk_train = np.asarray(risk_training_returns, dtype=float)
    if any(value.ndim != 2 for value in (x_train, r_train, x_val, r_val, risk_train)):
        raise ValueError("features, policy returns, and risk returns must be matrices")
    if x_train.shape[0] != r_train.shape[0] or x_val.shape[0] != r_val.shape[0]:
        raise ValueError("feature and policy-return rows must match")
    if x_train.shape[1] != x_val.shape[1] or r_train.shape[1] != r_val.shape[1]:
        raise ValueError("training and validation dimensions must match")
    assets = r_train.shape[1]
    if assets < 2 or risk_train.shape[1] != assets:
        raise ValueError("risk sample must contain the same assets as the policy problem")
    if min(x_train.shape[0], x_val.shape[0], risk_train.shape[0]) < 5:
        raise ValueError("at least five rows are required in each sample")
    if not all(np.all(np.isfinite(value)) for value in (x_train, r_train, x_val, r_val, risk_train)):
        raise ValueError("all numeric inputs must be finite")
    if maximum_asset_weight < 1.0 / assets or maximum_asset_weight > 1.0:
        raise ValueError("maximum_asset_weight must permit a fully invested portfolio")
    if maximum_turnover <= 0 or maximum_turnover > 2:
        raise ValueError("maximum_turnover must lie in (0,2]")
    if risk_aversion < 0 or transaction_cost < 0:
        raise ValueError("risk aversion and transaction cost must be nonnegative")
    if population_size < 10 or generations < 1 or not 0 < elite_fraction <= 0.5:
        raise ValueError("evolution settings are invalid")
    support_array = np.asarray(support_mask, dtype=bool)
    if maximum_calibration_off_support_correlation is not None:
        threshold = float(maximum_calibration_off_support_correlation)
        if not 0 <= threshold <= 1:
            raise ValueError("maximum calibration off-support correlation must lie in [0,1]")
        if risk_calibration_returns is None:
            raise ValueError("risk_calibration_returns are required for support-contradiction routing")
        calibration = np.asarray(risk_calibration_returns, dtype=float)
        if calibration.ndim != 2 or calibration.shape[1] != assets or calibration.shape[0] < 5 or not np.all(np.isfinite(calibration)):
            raise ValueError("risk calibration returns must be a finite matrix with the same assets")
        if support_array.shape != (assets, assets) or not np.array_equal(support_array, support_array.T):
            raise ValueError("support mask must be symmetric and match the policy assets")
        unsupported = np.logical_not(support_array)
        np.fill_diagonal(unsupported, False)
        if np.any(unsupported):
            correlations = np.corrcoef(calibration, rowvar=False)
            max_calibration_off_support = float(np.max(np.abs(correlations[unsupported])))
            if max_calibration_off_support > threshold:
                return {
                    "status": "ABSTAIN_SUPPORT_CONTRADICTED_BY_CALIBRATION",
                    "reason": "held-out calibration correlation exceeds the declared off-support tolerance",
                    "maximum_calibration_off_support_correlation": max_calibration_off_support,
                    "configured_off_support_correlation_limit": threshold,
                    "fallback": "ordinary CAPL or an explicitly chosen raw-covariance control may be run by the caller; SACAPL does not silently substitute a policy after support contradiction",
                }

    covariance_result = covariance_estimator(
        risk_train,
        support_mask,
        validation_returns=risk_calibration_returns,
        shrinkage_grid=shrinkage_grid,
    )
    supported_covariance = np.asarray(covariance_result.covariance, dtype=float)
    raw_covariance = np.cov(risk_train, rowvar=False, ddof=1)
    if raw_covariance.shape != (assets, assets) or not np.all(np.isfinite(raw_covariance)):
        raise RuntimeError("raw covariance comparator is unavailable")

    common = dict(
        maximum_asset_weight=maximum_asset_weight,
        maximum_turnover=maximum_turnover,
        risk_aversion=risk_aversion,
        transaction_cost=transaction_cost,
        population_size=population_size,
        generations=generations,
        elite_fraction=elite_fraction,
        seed=seed,
    )
    candidate_coefficients, candidate_training, candidate_evaluated = _learn_with_covariance_geometry(
        capl_module._policy_actions, x_train, r_train, supported_covariance, **common
    )
    control_coefficients, control_training, control_evaluated = _learn_with_covariance_geometry(
        capl_module._policy_actions, x_train, r_train, raw_covariance, **common
    )

    candidate_weights = capl_module._policy_actions(
        x_val, candidate_coefficients, maximum_asset_weight, maximum_turnover
    )
    control_weights = capl_module._policy_actions(
        x_val, control_coefficients, maximum_asset_weight, maximum_turnover
    )
    candidate_validation = capl_module._metrics(candidate_weights, r_val, risk_aversion, transaction_cost)
    control_validation = capl_module._metrics(control_weights, r_val, risk_aversion, transaction_cost)
    candidate_audit = capl_module._audit(candidate_weights, maximum_asset_weight, maximum_turnover)
    control_audit = capl_module._audit(control_weights, maximum_asset_weight, maximum_turnover)
    candidate_variance = float(candidate_validation.return_volatility ** 2)
    control_variance = float(control_validation.return_volatility ** 2)
    variance_change = None if control_variance <= 0 else float(candidate_variance / control_variance - 1.0)
    raw_off_support = np.logical_not(support_array)
    raw_off_support_max = float(np.max(np.abs(raw_covariance[raw_off_support]))) if np.any(raw_off_support) else 0.0
    coefficients_equal = bool(np.allclose(candidate_coefficients, control_coefficients, atol=1e-12, rtol=1e-12))

    candidate_violations = (
        candidate_audit.sum_violations
        + candidate_audit.lower_bound_violations
        + candidate_audit.upper_bound_violations
        + candidate_audit.turnover_violations
    )
    return {
        "selected_shrinkage": float(covariance_result.selected_shrinkage),
        "supported_covariance_condition_number": float(covariance_result.condition_number),
        "raw_covariance_condition_number": float(np.linalg.cond(raw_covariance)),
        "supported_off_support_max_abs_covariance": float(covariance_result.unsupported_max_absolute_covariance),
        "raw_off_support_max_abs_covariance": raw_off_support_max,
        "candidate_training_covariance_metrics": candidate_training.to_dict(),
        "control_training_covariance_metrics": control_training.to_dict(),
        "candidate_validation_metrics": asdict(candidate_validation),
        "control_validation_metrics": asdict(control_validation),
        "candidate_validation_audit": asdict(candidate_audit),
        "control_validation_audit": asdict(control_audit),
        "candidate_coefficients": tuple(tuple(map(float, row)) for row in candidate_coefficients),
        "control_coefficients": tuple(tuple(map(float, row)) for row in control_coefficients),
        "policies_identical": coefficients_equal,
        "candidate_evaluated": int(candidate_evaluated),
        "control_evaluated": int(control_evaluated),
        "validation_certainty_equivalent_gain_vs_raw_covariance": float(
            candidate_validation.certainty_equivalent - control_validation.certainty_equivalent
        ),
        "validation_variance_change_fraction_vs_raw_covariance": variance_change,
        "status": (
            "SUPPORT_COVARIANCE_CHANGED_CAPL_RISK_OBJECTIVE"
            if not coefficients_equal and candidate_violations == 0
            else "SUPPORT_COVARIANCE_COLLAPSED_TO_RAW_CONTROL"
            if coefficients_equal and candidate_violations == 0
            else "POLICY_RETURNED_WITH_ACTION_VIOLATIONS"
        ),
    }
