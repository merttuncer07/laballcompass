import json
from pathlib import Path
import numpy as np
if __package__:
    from .sanp import construct_support_aware_neutral_portfolio, compare_with_raw_sample_on_fresh_returns
else:
    from sanp import construct_support_aware_neutral_portfolio, compare_with_raw_sample_on_fresh_returns
if __package__:
    from .parents.enpc import construct_portfolio
else:
    from parents.enpc import construct_portfolio

SEED = 20260825


def main_covariance():
    covariance = np.eye(8) * 0.0004
    for i in range(0, 8, 2):
        covariance[i, i] = 0.0005 + 0.00005 * i
        covariance[i + 1, i + 1] = 0.0006 + 0.00004 * i
        covariance[i, i + 1] = covariance[i + 1, i] = 0.00020
    for i, j, value in [(0, 2, 0.00008), (2, 4, 0.00006), (4, 6, 0.00005)]:
        covariance[i, j] = covariance[j, i] = value
    return covariance


def adversarial_covariance():
    variances = np.array([0.001, 0.002, 0.0007, 0.0014, 0.0012, 0.0009])
    covariance = np.diag(variances)
    for i, j, rho in [(0, 1, -0.75), (2, 3, -0.60), (4, 5, 0.75)]:
        covariance[i, j] = covariance[j, i] = rho * np.sqrt(variances[i] * variances[j])
    return covariance


def fresh_variance(weights, returns):
    covariance = np.cov(returns, rowvar=False, ddof=1)
    return float(weights @ covariance @ weights)


def run_primary():
    rng = np.random.default_rng(SEED)
    covariance = main_covariance()
    data = rng.multivariate_normal(np.zeros(8), covariance, size=35 + 150 + 5000)
    train, validation, fresh = data[:35], data[35:185], data[185:]
    factors = np.array([[-1.0, -0.7, -0.4, -0.1, 0.1, 0.4, 0.7, 1.0]])
    kwargs = dict(factor_loadings=factors, target_factor_exposure=np.array([0.0]), lower_bounds=0.0, upper_bounds=0.35, risk_aversion=4.0)
    result = construct_support_aware_neutral_portfolio(
        train, np.abs(covariance) > 0, np.zeros(8), covariance_validation_returns=validation, **kwargs
    )
    comparison = compare_with_raw_sample_on_fresh_returns(result, train, np.zeros(8), fresh, **kwargs)
    sacps_weights = np.asarray(result.covariance_model.minimum_variance_weights)
    return {
        "seed": SEED, "train_cases": 35, "covariance_validation_cases": 150, "fresh_cases": 5000,
        "selected_shrinkage": result.covariance_model.selected_shrinkage,
        "raw_sample_condition_number": result.covariance_model.raw_sample_condition_number,
        "structured_condition_number": result.covariance_model.condition_number,
        "sanp_fresh_variance": comparison.support_aware_variance,
        "raw_enpc_fresh_variance": comparison.raw_sample_variance,
        "fresh_variance_change_fraction_vs_raw_enpc": comparison.variance_change_fraction_vs_raw,
        "fresh_variance_reduction_fraction_vs_raw_enpc": -comparison.variance_change_fraction_vs_raw,
        "sanp_factor_exposure": result.portfolio.factor_exposure.tolist(),
        "sanp_max_constraint_residual": result.portfolio.maximum_constraint_residual,
        "sanp_min_weight": float(np.min(result.portfolio.weights)),
        "sanp_max_weight": float(np.max(result.portfolio.weights)),
        "sacps_native_factor_exposure": float((factors @ sacps_weights)[0]),
        "sacps_native_min_weight": float(np.min(sacps_weights)),
        "sacps_native_max_weight": float(np.max(sacps_weights)),
    }


def run_support_misspecification():
    rng = np.random.default_rng(SEED)
    covariance = adversarial_covariance()
    data = rng.multivariate_normal(np.zeros(6), covariance, size=25 + 80 + 10000)
    train, validation, fresh = data[:25], data[25:105], data[105:]
    factors = np.linspace(-1.0, 1.0, 6)[None, :]
    kwargs = dict(factor_loadings=factors, target_factor_exposure=np.array([0.0]), lower_bounds=0.0, upper_bounds=0.5, risk_aversion=4.0)
    correct = construct_support_aware_neutral_portfolio(
        train, np.abs(covariance) > 0, np.zeros(6), covariance_validation_returns=validation, **kwargs
    )
    wrong = construct_support_aware_neutral_portfolio(
        train, np.eye(6, dtype=bool), np.zeros(6), covariance_validation_returns=validation, **kwargs
    )
    raw = construct_portfolio(np.zeros(6), np.cov(train, rowvar=False, ddof=1), **kwargs)
    correct_v = fresh_variance(correct.portfolio.weights, fresh)
    wrong_v = fresh_variance(wrong.portfolio.weights, fresh)
    raw_v = fresh_variance(raw.weights, fresh)
    return {
        "seed": SEED, "train_cases": 25, "covariance_validation_cases": 80, "fresh_cases": 10000,
        "correct_support_selected_shrinkage": correct.covariance_model.selected_shrinkage,
        "wrong_diagonal_support_selected_shrinkage": wrong.covariance_model.selected_shrinkage,
        "correct_support_fresh_variance": correct_v,
        "wrong_support_fresh_variance": wrong_v,
        "raw_enpc_fresh_variance": raw_v,
        "correct_support_change_fraction_vs_raw": correct_v / raw_v - 1.0,
        "wrong_support_change_fraction_vs_raw": wrong_v / raw_v - 1.0,
        "wrong_vs_correct_fraction": wrong_v / correct_v - 1.0,
        "interpretation": "Support compliance is not support correctness; a misspecified mask can degrade fresh risk even while all numerical and ENPC constraints pass."
    }


payload = {
    "product": "SANP v0.1",
    "route": "C / SACPS -> ENPC",
    "primary_sparse_support_benchmark": run_primary(),
    "support_misspecification_adversarial_benchmark": run_support_misspecification(),
    "evidence_label": "SYNTHETIC_FIXED_SEED_BENCHMARK_NOT_REAL_WORLD_PROOF"
}
Path(__file__).with_name("BENCHMARK_RESULT.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
