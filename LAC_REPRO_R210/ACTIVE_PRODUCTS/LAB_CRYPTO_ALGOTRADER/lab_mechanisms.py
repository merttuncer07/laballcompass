"""Lab-native decision mechanisms extracted for the product runtime.

Source lineage:
- V2P032 LMDE: memory closure -> reliability tempering -> effective diversity
  -> decision fluctuation guard.
- V2P033 DTEC: decision-loss and uncertainty gated transaction execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from statistics import NormalDist
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class LabMemoryDecisionResult:
    positions: tuple[float, ...]
    expected_next_returns: tuple[float, ...]
    aggregate_estimation_sd: tuple[float, ...]
    block_diagnostics: tuple[dict, ...]
    active_fraction: float
    mean_position: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DecisionTransactionExecutionResult:
    executed_positions: tuple[float, ...]
    accepted_entries: int
    accepted_exits: int
    rejected_by_cost: int
    rejected_by_fluctuation: int
    avoided_turnover: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CoreSatelliteResult:
    combined_positions: tuple[float, ...]
    core_active_fraction: float
    exposure_added: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DependenceHorizonResult:
    horizon: int
    lag_profile: tuple[float, ...]
    finite_sample_boundaries: tuple[float, ...]
    below_boundary: tuple[bool, ...]
    observations: int
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_information_dependence_horizon(
    series: Sequence[float],
    *,
    max_lag: int = 12,
    quantiles: Sequence[float] = (0.2, 0.35, 0.5, 0.65, 0.8),
    boundary_scale: float = 1.5,
    stable_run: int = 3,
) -> DependenceHorizonResult:
    """V2P046 IDHL empirical event-dependence horizon, not a mixing proof."""
    values = np.asarray(series, dtype=float)
    if (
        values.ndim != 1
        or len(values) < max(100, 8 * max_lag)
        or np.any(~np.isfinite(values))
    ):
        raise ValueError("finite series with adequate history required")
    if max_lag < 1 or stable_run < 1 or boundary_scale <= 0:
        raise ValueError("invalid horizon contract")
    cuts = np.quantile(values, tuple(float(value) for value in quantiles))
    profile: list[float] = []
    boundaries: list[float] = []
    for lag in range(1, max_lag + 1):
        past = values[:-lag]
        future = values[lag:]
        best = 0.0
        for past_cut in cuts:
            past_event = past <= past_cut
            for future_cut in cuts:
                future_event = future <= future_cut
                dependence = abs(
                    float(np.mean(past_event & future_event))
                    - float(np.mean(past_event)) * float(np.mean(future_event))
                )
                best = max(best, dependence)
        profile.append(best)
        boundaries.append(boundary_scale / math.sqrt(len(past)))
    below = [value <= boundary for value, boundary in zip(profile, boundaries)]
    horizon = max_lag
    for start in range(0, max_lag - stable_run + 1):
        if all(below[start : start + stable_run]):
            horizon = start + 1
            break
    return DependenceHorizonResult(
        horizon,
        tuple(profile),
        tuple(boundaries),
        tuple(below),
        len(values),
        "EMPIRICAL_EVENT_DEPENDENCE_HORIZON_NOT_POPULATION_MIXING_CERTIFICATE",
    )


def _rolling_mean(values: np.ndarray, window: int) -> np.ndarray:
    result = np.full(len(values), np.nan)
    if len(values) >= window:
        result[window - 1 :] = np.convolve(
            values, np.ones(window) / window, mode="valid"
        )
    return result


def allocate_core_satellite_exposure(
    close_prices: Sequence[float],
    tactical_positions: Sequence[float],
    *,
    fast_window: int = 64,
    slow_window: int = 256,
    core_position: float = 1.0,
) -> CoreSatelliteResult:
    """V2P031 CSAE: slow bull-regime core beneath tactical long/cash exposure."""
    close = np.asarray(close_prices, dtype=float)
    tactical = np.asarray(tactical_positions, dtype=float)
    if close.ndim != 1 or tactical.shape != close.shape or not np.all(np.isfinite(close)):
        raise ValueError("close and tactical vectors must align")
    if (
        np.any(tactical < 0)
        or np.any(tactical > 1)
        or not 1 < fast_window < slow_window
        or not 0 <= core_position <= 1
    ):
        raise ValueError("invalid core-satellite contract")
    fast = _rolling_mean(close, fast_window)
    slow = _rolling_mean(close, slow_window)
    bull = np.isfinite(slow) & (close > slow) & (fast > slow)
    core = np.where(bull, core_position, 0.0)
    combined = np.maximum(tactical, core)
    return CoreSatelliteResult(
        tuple(map(float, combined)),
        float(np.mean(bull)),
        float(np.sum(combined - tactical)),
        "SLOW_REGIME_CORE_PLUS_TACTICAL_SATELLITE",
    )


def _design(series: np.ndarray, lag: int, start: int, stop: int) -> tuple[np.ndarray, np.ndarray]:
    y = series[start:stop]
    design = np.column_stack(
        [np.ones(len(y))]
        + [series[start - offset - 1 : stop - offset - 1] for offset in range(lag)]
    )
    return design, y


def _fit_memory_kernel(
    series: np.ndarray, max_lag: int, min_relative_gain: float
) -> tuple[int, np.ndarray, float]:
    split = int(len(series) * 0.70)
    records: list[tuple[int, float]] = []
    for lag in range(1, max_lag + 1):
        x_train, y_train = _design(series, lag, lag, split)
        beta = np.linalg.lstsq(x_train, y_train, rcond=None)[0]
        x_valid, y_valid = _design(series, lag, split, len(series))
        rmse = float(np.sqrt(np.mean((y_valid - x_valid @ beta) ** 2)))
        records.append((lag, rmse))
    baseline = records[0][1]
    best_rmse = min(record[1] for record in records)
    candidate = min(
        (record for record in records if record[1] <= best_rmse * 1.002),
        key=lambda record: record[0],
    )
    gain = (baseline - candidate[1]) / max(baseline, 1e-15)
    lag = candidate[0] if candidate[0] > 1 and gain >= min_relative_gain else 1
    x_all, y_all = _design(series, lag, lag, len(series))
    beta = np.linalg.lstsq(x_all, y_all, rcond=None)[0]
    residual = y_all - x_all @ beta
    return lag, beta, float(np.var(residual, ddof=1))


def _forecast(beta: np.ndarray, lag: int, history: np.ndarray) -> float:
    lags = np.asarray([history[-offset - 1] for offset in range(lag)])
    return float(beta[0] + beta[1:] @ lags)


def _equicorrelation(matrix: np.ndarray) -> float:
    if matrix.shape[0] < 2 or matrix.shape[1] < 3:
        return 0.0
    correlation = np.corrcoef(matrix)
    values = correlation[np.triu_indices(len(correlation), 1)]
    values = values[np.isfinite(values)]
    rho = float(np.mean(values)) if len(values) else 0.0
    lower = -1.0 / (matrix.shape[0] - 1) + 1e-9
    return float(np.clip(rho, lower, 0.999999))


def _reliability_contract(
    series: np.ndarray, lag: int, beta: np.ndarray, direct_window: int
) -> dict:
    start = max(lag, direct_window, int(len(series) * 0.70))
    proxy: list[float] = []
    direct: list[float] = []
    actual: list[float] = []
    for index in range(start, len(series)):
        proxy.append(_forecast(beta, lag, series[:index]))
        direct.append(float(np.mean(series[index - direct_window : index])))
        actual.append(float(series[index]))
    proxy_values = np.asarray(proxy)
    direct_values = np.asarray(direct)
    actual_values = np.asarray(actual)
    proxy_error = proxy_values - actual_values
    direct_error = direct_values - actual_values
    floor = max(float(np.var(actual_values, ddof=1)) * 1e-6, 1e-16)
    proxy_variance = max(float(np.mean(proxy_error**2)), floor)
    direct_variance = max(float(np.mean(direct_error**2)), floor)
    proxy_weight = (1 / proxy_variance) / (1 / proxy_variance + 1 / direct_variance)
    return {
        "proxy_variance": proxy_variance,
        "direct_variance": direct_variance,
        "proxy_bias": float(np.mean(proxy_error)),
        "proxy_weight": float(proxy_weight),
        "calibration_count": int(len(actual_values)),
    }


def build_lab_memory_decision_positions(
    close_prices: Sequence[float],
    *,
    train_bars: int = 1500,
    test_bars: int = 192,
    purge_bars: int = 2,
    max_lag: int = 12,
    min_relative_gain: float = 0.005,
    decision_alpha: float = 0.30,
    direct_window: int = 18,
) -> LabMemoryDecisionResult:
    close = np.asarray(close_prices, dtype=float)
    if (
        close.ndim != 1
        or len(close) <= train_bars + test_bars
        or np.any(~np.isfinite(close))
        or np.any(close <= 0)
    ):
        raise ValueError("positive finite close series must exceed train_bars + test_bars")
    if purge_bars < 1 or max_lag < 1 or direct_window < 2 or not 0 < decision_alpha < 0.5:
        raise ValueError("invalid LMDE contract")

    returns = np.zeros(len(close))
    returns[1:] = np.diff(np.log(close))
    positions = np.zeros(len(close))
    expected_returns = np.zeros(len(close))
    aggregate_sds = np.zeros(len(close))
    diagnostics: list[dict] = []
    z_score = float(NormalDist().inv_cdf(1 - decision_alpha))

    for test_start in range(train_bars, len(close), test_bars):
        test_end = min(len(close), test_start + test_bars)
        train_end = test_start - purge_bars
        train_start = max(1, train_end - train_bars)
        train = returns[train_start:train_end]
        if len(train) < max(100, 20 * max_lag):
            continue

        lag, beta, residual_variance = _fit_memory_kernel(
            train, max_lag, min_relative_gain
        )
        reliability = _reliability_contract(train, lag, beta, direct_window)

        ensemble: list[tuple[int, np.ndarray]] = []
        segment = max(100, int(len(train) * 0.60))
        for offset in np.linspace(0, len(train) - segment, 4, dtype=int):
            sample = train[offset : offset + segment]
            ensemble_lag, ensemble_beta, _ = _fit_memory_kernel(
                sample, max_lag, min_relative_gain
            )
            ensemble.append((ensemble_lag, ensemble_beta))
        common_start = max(max(item[0] for item in ensemble), int(len(train) * 0.75))
        model_tracks = [
            [_forecast(item_beta, item_lag, train[:index]) for index in range(common_start, len(train))]
            for item_lag, item_beta in ensemble
        ]
        rho = _equicorrelation(np.asarray(model_tracks))
        nominal = len(ensemble)
        effective_count = nominal / max(1 + (nominal - 1) * rho, 1e-12)

        safe_count = 0
        block_positions: list[float] = []
        for index in range(test_start, test_end):
            history = returns[: index + 1]
            proxy = _forecast(beta, lag, history)
            direct = float(np.mean(history[-direct_window:]))
            weight = reliability["proxy_weight"]
            estimate = weight * (proxy - reliability["proxy_bias"]) + (1 - weight) * direct
            ensemble_forecasts = np.asarray(
                [_forecast(item_beta, item_lag, history) for item_lag, item_beta in ensemble]
            )
            model_se = float(
                np.std(ensemble_forecasts, ddof=1) / np.sqrt(max(effective_count, 1.0))
            )
            calibration_se = float(
                np.sqrt(
                    (
                        weight**2 * reliability["proxy_variance"]
                        + (1 - weight) ** 2 * reliability["direct_variance"]
                    )
                    / max(reliability["calibration_count"], 1)
                )
            )
            disagreement = 0.25 * abs((proxy - reliability["proxy_bias"]) - direct)
            aggregate_sd = max(
                float(np.sqrt(model_se**2 + calibration_se**2 + disagreement**2)),
                1e-12,
            )
            expected_returns[index] = estimate
            aggregate_sds[index] = aggregate_sd
            required_gap = z_score * aggregate_sd
            if estimate > 0 and abs(estimate) >= required_gap:
                position = min(1.0, 0.5 * abs(estimate) / max(required_gap, 1e-12))
                safe_count += 1
            else:
                position = 0.0
            positions[index] = position
            block_positions.append(position)

        diagnostics.append(
            {
                "test_start": test_start,
                "test_end": test_end,
                "selected_memory_lag": lag,
                "memory_promoted_beyond_markov1": bool(lag > 1),
                "proxy_weight": reliability["proxy_weight"],
                "effective_model_count": float(effective_count),
                "pairwise_model_correlation": float(rho),
                "residual_variance": residual_variance,
                "safe_long_fraction": safe_count / max(test_end - test_start, 1),
                "mean_raw_position": float(np.mean(block_positions)),
            }
        )

    evaluated = positions[train_bars:]
    return LabMemoryDecisionResult(
        tuple(map(float, positions)),
        tuple(map(float, expected_returns)),
        tuple(map(float, aggregate_sds)),
        tuple(diagnostics),
        float(np.mean(evaluated > 0)),
        float(np.mean(evaluated)),
        "LAB_MEMORY_RELIABILITY_DIVERSITY_DECISION_COMPOSITION",
    )


def control_decision_transaction_execution(
    desired_positions: Sequence[float],
    expected_next_returns: Sequence[float],
    aggregate_estimation_sd: Sequence[float],
    *,
    cost_per_side: float,
    decision_horizon: int = 8,
    alpha: float = 0.20,
) -> DecisionTransactionExecutionResult:
    desired = np.asarray(desired_positions, dtype=float)
    expected = np.asarray(expected_next_returns, dtype=float)
    uncertainty = np.asarray(aggregate_estimation_sd, dtype=float)
    if desired.ndim != 1 or expected.shape != desired.shape or uncertainty.shape != desired.shape:
        raise ValueError("desired, expected return and uncertainty vectors must align")
    if np.any(~np.isfinite(desired)) or np.any(~np.isfinite(expected)) or np.any(~np.isfinite(uncertainty)):
        raise ValueError("inputs must be finite")
    if np.any(desired < 0) or np.any(desired > 1) or np.any(uncertainty < 0):
        raise ValueError("long/cash positions and nonnegative uncertainty required")
    if cost_per_side < 0 or decision_horizon < 1 or not 0 < alpha < 0.5:
        raise ValueError("invalid execution contract")

    z_score = float(NormalDist().inv_cdf(1 - alpha))
    executed = np.zeros(len(desired))
    current = 0.0
    entries = exits = rejected_cost = rejected_fluctuation = 0
    for index, target in enumerate(desired):
        target = float(target)
        candidate = current
        if current <= 1e-12 and target > 1e-12:
            candidate = target
        elif current > 1e-12 and target <= 1e-12:
            candidate = 0.0
        if abs(candidate - current) <= 1e-12:
            executed[index] = current
            continue
        hold_payoff = current * float(expected[index]) * decision_horizon
        switch_payoff = (
            candidate * float(expected[index]) * decision_horizon
            - cost_per_side * abs(candidate - current)
        )
        gap = abs(switch_payoff - hold_payoff)
        required_gap = (
            z_score
            * float(uncertainty[index])
            * decision_horizon
            * abs(candidate - current)
        )
        if switch_payoff <= hold_payoff:
            rejected_cost += 1
        elif gap < required_gap:
            rejected_fluctuation += 1
        else:
            if candidate > current:
                entries += 1
            else:
                exits += 1
            current = candidate
        executed[index] = current

    raw_turnover = float(np.sum(np.abs(np.diff(np.r_[0.0, desired]))))
    executed_turnover = float(np.sum(np.abs(np.diff(np.r_[0.0, executed]))))
    return DecisionTransactionExecutionResult(
        tuple(map(float, executed)),
        entries,
        exits,
        rejected_cost,
        rejected_fluctuation,
        raw_turnover - executed_turnover,
        "DECISION_LOSS_AND_FLUCTUATION_GATED_EXECUTION",
    )
