"""Compare a neutral portfolio with an unconstrained mean-variance portfolio."""

from __future__ import annotations

import json

import numpy as np

from enpc import construct_portfolio


def serializable(solution):
    return {
        "weights": solution.weights.tolist(),
        "expected_return": solution.expected_return,
        "volatility": solution.volatility,
        "objective_value": solution.objective_value,
        "factor_exposure": solution.factor_exposure.tolist(),
        "budget_residual": solution.budget_residual,
        "maximum_constraint_residual": solution.maximum_constraint_residual,
        "neutral_subspace_dimension": solution.neutral_subspace_dimension,
    }


def main() -> None:
    factors = np.array(
        [
            [1.0, 0.9, 0.2, 0.1, -0.8, -1.0],
            [0.8, -0.5, 1.0, -1.0, 0.3, -0.6],
        ]
    )
    alpha = np.array([0.025, 0.018, 0.020, 0.016, 0.012, 0.010])
    factor_premium = np.array([0.10, 0.04])
    mu = alpha + factors.T @ factor_premium
    factor_covariance = np.diag([0.05, 0.035])
    covariance = factors.T @ factor_covariance @ factors + np.diag([0.025] * 6)
    neutral = construct_portfolio(mu, covariance, factors, np.zeros(2), risk_aversion=3.0)
    unconstrained = construct_portfolio(mu, covariance, risk_aversion=3.0)
    stress_factors = np.array([[0.0, -0.35], [-0.25, 0.0], [-0.25, -0.35], [0.25, 0.35]])
    neutral_stress = stress_factors @ (factors @ neutral.weights)
    unconstrained_stress = stress_factors @ (factors @ unconstrained.weights)
    output = {
        "neutral_portfolio": serializable(neutral),
        "unconstrained_portfolio": serializable(unconstrained),
        "nominal_expected_return_cost_of_neutrality": unconstrained.expected_return - neutral.expected_return,
        "factor_stress_returns": {
            "neutral": neutral_stress.tolist(),
            "unconstrained": unconstrained_stress.tolist(),
            "unconstrained_worst_loss": float(np.min(unconstrained_stress)),
            "neutral_worst_loss": float(np.min(neutral_stress)),
        },
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

