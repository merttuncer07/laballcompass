from __future__ import annotations

import numpy as np


def transform_to_x(y: np.ndarray, curvature: float = 2.0) -> np.ndarray:
    return np.sinh(curvature * y) / curvature


def transform_to_y(x: np.ndarray, curvature: float = 2.0) -> np.ndarray:
    return np.arcsinh(curvature * x) / curvature


def sigma_x(x: np.ndarray, curvature: float = 2.0) -> np.ndarray:
    return np.sqrt(1.0 + (curvature * x) ** 2)


def beta_y(y: np.ndarray, offsets: np.ndarray, contraction: float = 1.2):
    return -contraction * np.tanh(y) + offsets


def drift_x(
    x: np.ndarray,
    offsets: np.ndarray,
    contraction: float = 1.2,
    curvature: float = 2.0,
):
    y = transform_to_y(x, curvature)
    sigma = sigma_x(x, curvature)
    # Ito image of dY = beta(Y)dt + dW under X=sinh(cY)/c.
    return sigma * beta_y(y, offsets, contraction) + 0.5 * curvature**2 * x


def _order_failure(states: np.ndarray) -> np.ndarray:
    return (states[:, 0] > states[:, 1]) | (states[:, 1] > states[:, 2])


def simulate_raw_euler(
    paths: int,
    steps: int,
    horizon: float = 1.0,
    seed: int = 0,
    delta: float = 0.55,
    contraction: float = 1.2,
    curvature: float = 2.0,
):
    rng = np.random.default_rng(seed)
    dt = horizon / steps
    offsets = np.array([-delta, 0.0, delta])
    states = np.zeros((paths, 3))
    ever_failed = np.zeros(paths, dtype=bool)
    nonfinite = np.zeros(paths, dtype=bool)
    for _ in range(steps):
        noise = rng.normal(size=(paths, 1))
        states = (
            states
            + drift_x(states, offsets, contraction, curvature) * dt
            + sigma_x(states, curvature) * np.sqrt(dt) * noise
        )
        nonfinite |= ~np.all(np.isfinite(states), axis=1)
        ever_failed |= _order_failure(states)
    return {
        "states": states,
        "order_failure_rate": float(np.mean(ever_failed)),
        "nonfinite_rate": float(np.mean(nonfinite)),
    }


def simulate_transformed_euler(
    paths: int,
    steps: int,
    horizon: float = 1.0,
    seed: int = 0,
    delta: float = 0.55,
    contraction: float = 1.2,
    curvature: float = 2.0,
):
    rng = np.random.default_rng(seed)
    dt = horizon / steps
    offsets = np.array([-delta, 0.0, delta])
    states_y = np.zeros((paths, 3))
    ever_failed = np.zeros(paths, dtype=bool)
    for _ in range(steps):
        noise = rng.normal(size=(paths, 1))
        states_y = (
            states_y
            + beta_y(states_y, offsets, contraction) * dt
            + np.sqrt(dt) * noise
        )
        ever_failed |= _order_failure(states_y)
    states_x = transform_to_x(states_y, curvature)
    return {
        "states": states_x,
        "order_failure_rate": float(np.mean(ever_failed)),
        "nonfinite_rate": float(np.mean(~np.all(np.isfinite(states_x), axis=1))),
    }


def cdf_order_violations(states: np.ndarray, grid_size: int = 201):
    finite = states[np.all(np.isfinite(states), axis=1)]
    low = float(np.quantile(finite, 0.005))
    high = float(np.quantile(finite, 0.995))
    grid = np.linspace(low, high, grid_size)
    cdfs = np.stack([(finite[:, index, None] <= grid).mean(axis=0) for index in range(3)])
    # X_minus <= X_mid <= X_plus implies F_minus >= F_mid >= F_plus.
    violation = np.maximum(cdfs[1] - cdfs[0], cdfs[2] - cdfs[1])
    return {
        "grid_size": grid_size,
        "max_empirical_cdf_order_violation": float(np.max(violation)),
    }

