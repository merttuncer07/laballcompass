"""Support-Aware Neutral Portfolio (SANP) v0.1.

A directed SACPS -> ENPC composition. SACPS estimates a support-constrained,
regularized covariance; ENPC consumes that covariance while imposing budget,
factor-exposure, and position-bound constraints.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

if __package__:
    from .parents.enpc import PortfolioSolution, construct_portfolio
else:
    from parents.enpc import PortfolioSolution, construct_portfolio
if __package__:
    from .parents.sacps import CovarianceDecisionResult, estimate_support_aware_covariance
else:
    from parents.sacps import CovarianceDecisionResult, estimate_support_aware_covariance


@dataclass(frozen=True)
class SupportAwareNeutralPortfolioResult:
    covariance_model: CovarianceDecisionResult
    portfolio: PortfolioSolution
    training_cases: int
    covariance_validation_cases: int
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FreshRiskComparison:
    support_aware_variance: float
    raw_sample_variance: float
    variance_change_fraction_vs_raw: float
    support_aware_volatility: float
    raw_sample_volatility: float
    cases: int
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _returns_matrix(values: Sequence[Sequence[float]], name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[0] < 2 or array.shape[1] < 2 or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite case-by-asset matrix")
    return array


def construct_support_aware_neutral_portfolio(
    training_returns: Sequence[Sequence[float]],
    support_mask: Sequence[Sequence[bool]],
    expected_returns: Sequence[float],
    *,
    covariance_validation_returns: Sequence[Sequence[float]] | None = None,
    factor_loadings: Sequence[Sequence[float]] | None = None,
    target_factor_exposure: Sequence[float] | None = None,
    budget: float = 1.0,
    lower_bounds: Sequence[float] | float = -0.5,
    upper_bounds: Sequence[float] | float = 0.8,
    risk_aversion: float = 4.0,
    shrinkage_grid: Sequence[float] = tuple(np.linspace(0.0, 1.0, 21)),
    eigenvalue_floor: float = 1e-8,
    maximum_condition_number: float = 1e8,
) -> SupportAwareNeutralPortfolioResult:
    """Estimate covariance with SACPS, then solve the constrained portfolio with ENPC.

    `covariance_validation_returns` may tune SACPS shrinkage but is not used to
    evaluate the returned portfolio. Fresh evaluation must be kept separate.
    """
    train = _returns_matrix(training_returns, "training_returns")
    mu = np.asarray(expected_returns, dtype=float)
    if mu.shape != (train.shape[1],) or not np.all(np.isfinite(mu)):
        raise ValueError("expected_returns must contain one finite value per asset")
    validation = None
    if covariance_validation_returns is not None:
        validation = _returns_matrix(covariance_validation_returns, "covariance_validation_returns")
        if validation.shape[1] != train.shape[1]:
            raise ValueError("covariance validation asset dimension differs from training")

    covariance_model = estimate_support_aware_covariance(
        train,
        support_mask,
        validation_returns=validation,
        shrinkage_grid=shrinkage_grid,
        eigenvalue_floor=eigenvalue_floor,
        maximum_condition_number=maximum_condition_number,
    )
    covariance = np.asarray(covariance_model.covariance, dtype=float)
    factors = None if factor_loadings is None else np.asarray(factor_loadings, dtype=float)
    target = None if target_factor_exposure is None else np.asarray(target_factor_exposure, dtype=float)
    portfolio = construct_portfolio(
        mu,
        covariance,
        factor_loadings=factors,
        target_factor_exposure=target,
        budget=budget,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        risk_aversion=risk_aversion,
    )
    return SupportAwareNeutralPortfolioResult(
        covariance_model=covariance_model,
        portfolio=portfolio,
        training_cases=int(train.shape[0]),
        covariance_validation_cases=0 if validation is None else int(validation.shape[0]),
        status="SUPPORT_AWARE_COVARIANCE_CONSUMED_BY_NEUTRAL_PORTFOLIO",
    )


def compare_with_raw_sample_on_fresh_returns(
    result: SupportAwareNeutralPortfolioResult,
    training_returns: Sequence[Sequence[float]],
    expected_returns: Sequence[float],
    fresh_returns: Sequence[Sequence[float]],
    *,
    factor_loadings: Sequence[Sequence[float]] | None = None,
    target_factor_exposure: Sequence[float] | None = None,
    budget: float = 1.0,
    lower_bounds: Sequence[float] | float = -0.5,
    upper_bounds: Sequence[float] | float = 0.8,
    risk_aversion: float = 4.0,
) -> FreshRiskComparison:
    """Compare SANP with the same ENPC problem using raw training covariance.

    Fresh returns are used only after both portfolios have been constructed.
    """
    train = _returns_matrix(training_returns, "training_returns")
    fresh = _returns_matrix(fresh_returns, "fresh_returns")
    if fresh.shape[1] != train.shape[1]:
        raise ValueError("fresh return asset dimension differs from training")
    mu = np.asarray(expected_returns, dtype=float)
    raw_covariance = np.cov(train, rowvar=False, ddof=1)
    factors = None if factor_loadings is None else np.asarray(factor_loadings, dtype=float)
    target = None if target_factor_exposure is None else np.asarray(target_factor_exposure, dtype=float)
    raw_portfolio = construct_portfolio(
        mu,
        raw_covariance,
        factor_loadings=factors,
        target_factor_exposure=target,
        budget=budget,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        risk_aversion=risk_aversion,
    )
    if result.portfolio.weights.shape != raw_portfolio.weights.shape:
        raise ValueError("result portfolio dimension differs from training returns")
    fresh_covariance = np.cov(fresh, rowvar=False, ddof=1)
    structured_variance = float(result.portfolio.weights @ fresh_covariance @ result.portfolio.weights)
    raw_variance = float(raw_portfolio.weights @ fresh_covariance @ raw_portfolio.weights)
    change = float(structured_variance / raw_variance - 1.0) if raw_variance > 0 else float("nan")
    return FreshRiskComparison(
        support_aware_variance=structured_variance,
        raw_sample_variance=raw_variance,
        variance_change_fraction_vs_raw=change,
        support_aware_volatility=float(np.sqrt(max(0.0, structured_variance))),
        raw_sample_volatility=float(np.sqrt(max(0.0, raw_variance))),
        cases=int(fresh.shape[0]),
        status="FRESH_OUT_OF_SAMPLE_RISK_COMPARISON",
    )
