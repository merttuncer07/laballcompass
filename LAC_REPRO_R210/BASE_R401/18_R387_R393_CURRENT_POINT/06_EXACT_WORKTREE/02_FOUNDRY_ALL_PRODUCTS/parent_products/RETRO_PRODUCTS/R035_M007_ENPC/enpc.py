"""Exposure-Neutral Portfolio Constructor (ENPC)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog, minimize


@dataclass(frozen=True)
class PortfolioSolution:
    weights: np.ndarray
    expected_return: float
    volatility: float
    objective_value: float
    factor_exposure: np.ndarray
    budget_residual: float
    maximum_constraint_residual: float
    neutral_subspace_dimension: int


def _validate_covariance(covariance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("covariance must be square")
    if not np.allclose(matrix, matrix.T, atol=1e-10):
        raise ValueError("covariance must be symmetric")
    if np.min(np.linalg.eigvalsh(matrix)) < -1e-10:
        raise ValueError("covariance must be positive semidefinite")
    return matrix


def construct_portfolio(
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    factor_loadings: np.ndarray | None = None,
    target_factor_exposure: np.ndarray | None = None,
    budget: float = 1.0,
    lower_bounds: np.ndarray | float = -0.5,
    upper_bounds: np.ndarray | float = 0.8,
    risk_aversion: float = 4.0,
) -> PortfolioSolution:
    mu = np.asarray(expected_returns, dtype=float)
    sigma = _validate_covariance(covariance)
    n = mu.size
    if sigma.shape != (n, n):
        raise ValueError("return and covariance dimensions differ")
    lower = np.broadcast_to(np.asarray(lower_bounds, dtype=float), (n,)).copy()
    upper = np.broadcast_to(np.asarray(upper_bounds, dtype=float), (n,)).copy()
    if factor_loadings is None:
        factors = np.zeros((0, n))
        target = np.zeros(0)
    else:
        factors = np.atleast_2d(np.asarray(factor_loadings, dtype=float))
        if factors.shape[1] != n:
            raise ValueError("factor loading dimension differs")
        target = (
            np.zeros(factors.shape[0])
            if target_factor_exposure is None
            else np.asarray(target_factor_exposure, dtype=float)
        )
        if target.shape != (factors.shape[0],):
            raise ValueError("target factor exposure dimension differs")
    equality_matrix = np.vstack([np.ones(n), factors])
    equality_rhs = np.concatenate([[budget], target])
    feasibility = linprog(
        np.zeros(n),
        A_eq=equality_matrix,
        b_eq=equality_rhs,
        bounds=list(zip(lower, upper)),
        method="highs",
    )
    if not feasibility.success:
        raise ValueError(f"requested budget/exposure is infeasible under bounds: {feasibility.message}")

    def objective(weights: np.ndarray) -> float:
        return float(0.5 * risk_aversion * weights @ sigma @ weights - mu @ weights)

    def gradient(weights: np.ndarray) -> np.ndarray:
        return risk_aversion * sigma @ weights - mu

    solved = minimize(
        objective,
        feasibility.x,
        jac=gradient,
        method="SLSQP",
        bounds=list(zip(lower, upper)),
        constraints={"type": "eq", "fun": lambda w: equality_matrix @ w - equality_rhs},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not solved.success:
        raise RuntimeError(solved.message)
    weights = np.asarray(solved.x)
    exposure = factors @ weights
    residual = equality_matrix @ weights - equality_rhs
    rank = np.linalg.matrix_rank(equality_matrix, tol=1e-10)
    return PortfolioSolution(
        weights=weights,
        expected_return=float(mu @ weights),
        volatility=float(np.sqrt(max(0.0, weights @ sigma @ weights))),
        objective_value=float(objective(weights)),
        factor_exposure=exposure,
        budget_residual=float(abs(weights.sum() - budget)),
        maximum_constraint_residual=float(np.max(np.abs(residual))),
        neutral_subspace_dimension=int(n - rank),
    )

