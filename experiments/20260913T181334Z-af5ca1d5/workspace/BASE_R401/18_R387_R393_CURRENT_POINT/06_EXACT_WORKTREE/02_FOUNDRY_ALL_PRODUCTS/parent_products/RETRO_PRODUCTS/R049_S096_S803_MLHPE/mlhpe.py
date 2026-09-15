"""Multi-List Hidden Population Estimator (MLHPE) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Mapping, Sequence

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln


@dataclass(frozen=True)
class ChapmanEstimate:
    list_one: int
    list_two: int
    overlap: int
    population_estimate: float
    standard_error: float
    unseen_estimate: float


@dataclass(frozen=True)
class LogLinearEstimate:
    model: str
    interactions: tuple[str, ...]
    parameters: int
    residual_degrees_of_freedom: int
    converged: bool
    status: str
    log_likelihood: float
    aic: float
    bic: float
    unseen_estimate: float
    unseen_confidence_low: float
    unseen_confidence_high: float
    total_population_estimate: float
    interaction_multipliers: dict[str, float]
    maximum_absolute_pearson_residual: float
    akaike_weight: float


@dataclass(frozen=True)
class MultiListAudit:
    observed_population: int
    models: tuple[LogLinearEstimate, ...]
    best_aic_model: str
    best_aic_total: float
    model_averaged_total: float
    total_estimate_minimum: float
    total_estimate_maximum: float
    total_estimate_ratio: float
    dependence_sensitivity: str
    saturated_models_excluded_from_selection: bool

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["models"] = [asdict(item) for item in self.models]
        return payload


def chapman_two_list(list_one: int, list_two: int, overlap: int) -> ChapmanEstimate:
    """Bias-corrected two-list population estimate and classical variance approximation."""

    if any(not isinstance(value, (int, np.integer)) or value < 0 for value in (list_one, list_two, overlap)):
        raise ValueError("list sizes and overlap must be non-negative integers")
    if overlap > min(list_one, list_two):
        raise ValueError("overlap cannot exceed either list size")
    estimate = ((list_one + 1) * (list_two + 1) / (overlap + 1)) - 1
    variance = (
        (list_one + 1) * (list_two + 1) * (list_one - overlap) * (list_two - overlap)
        / ((overlap + 1) ** 2 * (overlap + 2))
    )
    observed_union = list_one + list_two - overlap
    return ChapmanEstimate(
        list_one, list_two, overlap, float(estimate), float(np.sqrt(variance)),
        float(max(0.0, estimate - observed_union)),
    )


def _design(histories: Sequence[str], interactions: Sequence[tuple[int, int]]) -> np.ndarray:
    rows = []
    for history in histories:
        bits = np.asarray([int(value) for value in history], dtype=float)
        rows.append([1.0, *bits, *(bits[i] * bits[j] for i, j in interactions)])
    return np.asarray(rows, dtype=float)


def audit_three_lists(
    capture_history_counts: Mapping[str, int],
    *,
    include_interaction_orders: Sequence[int] = (0, 1, 2, 3),
    confidence_z: float = 1.96,
) -> MultiListAudit:
    """Fit independence and selected pairwise-interaction Poisson log-linear models."""

    histories = ("001", "010", "011", "100", "101", "110", "111")
    if set(capture_history_counts) != set(histories):
        raise ValueError("counts must provide exactly the seven observed three-list histories")
    if any(not isinstance(value, (int, np.integer)) or value < 0 for value in capture_history_counts.values()):
        raise ValueError("capture-history counts must be non-negative integers")
    if sum(capture_history_counts.values()) <= 0 or confidence_z <= 0:
        raise ValueError("at least one individual must be observed and confidence_z positive")
    orders = tuple(sorted(set(include_interaction_orders)))
    if any(order not in (0, 1, 2, 3) for order in orders) or not orders:
        raise ValueError("interaction orders must be selected from 0,1,2,3")

    y = np.asarray([capture_history_counts[history] for history in histories], dtype=float)
    observed = int(np.sum(y))
    pair_defs = (((0, 1), "AB"), ((0, 2), "AC"), ((1, 2), "BC"))
    model_specs: list[tuple[tuple[tuple[int, int], ...], tuple[str, ...]]] = []
    for order in orders:
        for chosen in combinations(pair_defs, order):
            model_specs.append((tuple(item[0] for item in chosen), tuple(item[1] for item in chosen)))

    provisional: list[dict] = []
    for interaction_pairs, labels in model_specs:
        x = _design(histories, interaction_pairs)

        def objective(beta: np.ndarray) -> float:
            linear = np.clip(x @ beta, -30.0, 30.0)
            return float(np.sum(np.exp(linear) - y * linear + gammaln(y + 1)))

        def gradient(beta: np.ndarray) -> np.ndarray:
            linear = np.clip(x @ beta, -30.0, 30.0)
            return x.T @ (np.exp(linear) - y)

        initial = np.zeros(x.shape[1])
        initial[0] = np.log(max(float(np.mean(y)), 1e-6))
        fit = minimize(objective, initial, jac=gradient, method="L-BFGS-B", bounds=[(-30, 30)] * x.shape[1])
        beta = fit.x
        mu = np.exp(np.clip(x @ beta, -30.0, 30.0))
        log_likelihood = float(np.sum(y * np.log(mu) - mu - gammaln(y + 1)))
        k = x.shape[1]
        hessian = x.T @ (x * mu[:, None])
        covariance = np.linalg.pinv(hessian)
        intercept_se = float(np.sqrt(max(covariance[0, 0], 0.0)))
        unseen = float(np.exp(np.clip(beta[0], -30.0, 30.0)))
        pearson = (y - mu) / np.sqrt(np.maximum(mu, 1e-15))
        df = len(histories) - k
        status = "SATURATED_OBSERVED_TABLE" if df == 0 else "ESTIMATED_WITH_RESIDUAL_DF"
        provisional.append({
            "model": "independence" if not labels else "+".join(labels),
            "interactions": labels,
            "parameters": k,
            "residual_degrees_of_freedom": df,
            "converged": bool(fit.success),
            "status": status if fit.success else "OPTIMIZER_WARNING",
            "log_likelihood": log_likelihood,
            "aic": float(2 * k - 2 * log_likelihood),
            "bic": float(k * np.log(observed) - 2 * log_likelihood),
            "unseen_estimate": unseen,
            "unseen_confidence_low": float(np.exp(np.clip(beta[0] - confidence_z * intercept_se, -30, 30))),
            "unseen_confidence_high": float(np.exp(np.clip(beta[0] + confidence_z * intercept_se, -30, 30))),
            "total_population_estimate": observed + unseen,
            "interaction_multipliers": {
                label: float(np.exp(np.clip(beta[4 + index], -30, 30))) for index, label in enumerate(labels)
            },
            "maximum_absolute_pearson_residual": float(np.max(np.abs(pearson))),
        })

    usable = [item for item in provisional if item["converged"]]
    if not usable:
        raise RuntimeError("no log-linear model converged")
    eligible = [item for item in usable if item["residual_degrees_of_freedom"] > 0]
    if not eligible:
        raise RuntimeError("no model with residual degrees of freedom converged")
    minimum_aic = min(item["aic"] for item in eligible)
    raw_weights = np.asarray([np.exp(-0.5 * (item["aic"] - minimum_aic)) for item in eligible])
    raw_weights /= np.sum(raw_weights)
    weight_by_model = {item["model"]: float(weight) for item, weight in zip(eligible, raw_weights)}
    models = tuple(LogLinearEstimate(**item, akaike_weight=weight_by_model.get(item["model"], 0.0)) for item in provisional)
    best = min(eligible, key=lambda item: item["aic"])
    totals = np.asarray([item["total_population_estimate"] for item in usable])
    averaged = float(sum(item["total_population_estimate"] * weight_by_model[item["model"]] for item in eligible))
    ratio = float(np.max(totals) / np.min(totals))
    sensitivity = "HIGH" if ratio >= 1.5 else "MODERATE" if ratio >= 1.15 else "LOW"
    return MultiListAudit(
        observed, models, best["model"], float(best["total_population_estimate"]), averaged,
        float(np.min(totals)), float(np.max(totals)), ratio, sensitivity, len(eligible) < len(usable),
    )
