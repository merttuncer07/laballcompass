"""Paper-only, market-neutral spot/perpetual funding-basis research engine.

The engine deliberately contains no authenticated exchange client.  It reconstructs
the public mechanism used by professional crypto liquidity/arbitrage desks: price a
hedgeable two-leg trade, require edge above uncertainty and costs, and preserve the
position only while that inequality remains favorable.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any, Mapping, Sequence
import urllib.parse
import urllib.request

import numpy as np

from lab_mechanisms import control_decision_transaction_execution


FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
SPOT_KLINE_URL = "https://data-api.binance.vision/api/v3/klines"
EIGHT_HOURS_MS = 8 * 60 * 60 * 1000


@dataclass(frozen=True)
class CarryData:
    timestamp_ms: np.ndarray
    spot_price: np.ndarray
    perp_mark_price: np.ndarray
    funding_rate: np.ndarray
    symbol: str
    source: str
    sha256: str = ""

    def __len__(self) -> int:
        return len(self.timestamp_ms)


@dataclass(frozen=True)
class CarrySignal:
    desired_positions: tuple[float, ...]
    expected_carry: tuple[float, ...]
    estimation_sd: tuple[float, ...]
    funding_forecast: tuple[float, ...]
    basis_reversion_forecast: tuple[float, ...]
    reliability_weight: tuple[float, ...]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _json_get(url: str, params: Mapping[str, Any], timeout_seconds: int = 30) -> Any:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{url}?{query}", headers={"User-Agent": "LabCryptoCarryResearch/1.0"}
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_backwards(
    url: str,
    fixed_params: Mapping[str, Any],
    bars: int,
    *,
    timeout_seconds: int,
) -> list[Any]:
    rows: list[Any] = []
    end_time: int | None = None
    while len(rows) < bars:
        params = dict(fixed_params)
        params["limit"] = min(1000, bars - len(rows))
        if end_time is not None:
            params["endTime"] = end_time
        batch = _json_get(url, params, timeout_seconds)
        if not batch:
            break
        rows.extend(batch)
        first_time = min(
            int(row[0]) if isinstance(row, list) else int(row["fundingTime"])
            for row in batch
        )
        next_end = first_time - 1
        if end_time is not None and next_end >= end_time:
            break
        end_time = next_end
    return rows


def fetch_public_carry_data(
    symbol: str,
    bars: int = 1500,
    *,
    timeout_seconds: int = 30,
) -> CarryData:
    """Download settled funding records and executable spot-price proxies.

    Binance funding timestamps occasionally differ from the nominal 8-hour boundary
    by a few milliseconds.  They are matched to the nearest 8-hour spot candle open.
    Only symbols whose observed settlements align to that grid are retained.
    """
    if bars < 200 or bars > 5000:
        raise ValueError("bars must be between 200 and 5000")
    symbol = symbol.upper()
    funding_rows = _fetch_backwards(
        FUNDING_URL,
        {"symbol": symbol},
        bars,
        timeout_seconds=timeout_seconds,
    )
    if len(funding_rows) < 200:
        raise ValueError(f"insufficient public funding history for {symbol}")
    funding_by_time: dict[int, tuple[float, float]] = {}
    for row in funding_rows:
        nominal = int(round(int(row["fundingTime"]) / EIGHT_HOURS_MS) * EIGHT_HOURS_MS)
        if abs(int(row["fundingTime"]) - nominal) <= 60_000:
            funding_by_time[nominal] = (float(row["fundingRate"]), float(row["markPrice"]))

    spot_rows = _fetch_backwards(
        SPOT_KLINE_URL,
        {"symbol": symbol, "interval": "8h"},
        bars + 20,
        timeout_seconds=timeout_seconds,
    )
    spot_by_time = {int(row[0]): float(row[1]) for row in spot_rows}
    common = sorted(set(funding_by_time).intersection(spot_by_time))[-bars:]
    if len(common) < 200:
        raise ValueError(f"could not align at least 200 funding and spot records for {symbol}")
    return CarryData(
        np.asarray(common, dtype=np.int64),
        np.asarray([spot_by_time[timestamp] for timestamp in common], dtype=float),
        np.asarray([funding_by_time[timestamp][1] for timestamp in common], dtype=float),
        np.asarray([funding_by_time[timestamp][0] for timestamp in common], dtype=float),
        symbol,
        "Binance public settled funding history + public 8h spot candle opens",
    )


def _validate(data: CarryData) -> None:
    arrays = (data.timestamp_ms, data.spot_price, data.perp_mark_price, data.funding_rate)
    if len({len(values) for values in arrays}) != 1 or len(data) < 200:
        raise ValueError("aligned carry arrays with at least 200 rows required")
    if any(np.asarray(values).ndim != 1 for values in arrays):
        raise ValueError("carry data must be one-dimensional")
    if any(np.any(~np.isfinite(values)) for values in arrays):
        raise ValueError("carry data must be finite")
    if np.any(np.diff(data.timestamp_ms) <= 0):
        raise ValueError("timestamps must increase")
    if np.any(data.spot_price <= 0) or np.any(data.perp_mark_price <= 0):
        raise ValueError("prices must be positive")


def save_carry_csv(data: CarryData, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("timestamp_ms", "spot_price", "perp_mark_price", "funding_rate"))
        writer.writerows(
            zip(data.timestamp_ms, data.spot_price, data.perp_mark_price, data.funding_rate)
        )


def load_carry_csv(path: Path, symbol: str) -> CarryData:
    columns: list[list[float]] = [[], [], [], []]
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = {"timestamp_ms", "spot_price", "perp_mark_price", "funding_rate"}
        if set(reader.fieldnames or ()) != expected:
            raise ValueError("unexpected carry CSV schema")
        for row in reader:
            columns[0].append(int(row["timestamp_ms"]))
            columns[1].append(float(row["spot_price"]))
            columns[2].append(float(row["perp_mark_price"]))
            columns[3].append(float(row["funding_rate"]))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    data = CarryData(
        np.asarray(columns[0], dtype=np.int64),
        np.asarray(columns[1], dtype=float),
        np.asarray(columns[2], dtype=float),
        np.asarray(columns[3], dtype=float),
        symbol.upper(),
        str(path.resolve()),
        digest,
    )
    _validate(data)
    return data


def slice_carry_data(data: CarryData, start: int, stop: int) -> CarryData:
    _validate(data)
    if start < 0 or stop > len(data) or stop - start < 200:
        raise ValueError("invalid carry slice")
    return CarryData(
        data.timestamp_ms[start:stop].copy(),
        data.spot_price[start:stop].copy(),
        data.perp_mark_price[start:stop].copy(),
        data.funding_rate[start:stop].copy(),
        data.symbol,
        f"{data.source} rows[{start}:{stop}]",
        data.sha256,
    )


def realized_carry(data: CarryData) -> np.ndarray:
    """Per-unit-notional long-spot/short-perpetual return at each settlement."""
    _validate(data)
    result = np.zeros(len(data))
    result[1:] = (
        np.diff(np.log(data.spot_price))
        - np.diff(np.log(data.perp_mark_price))
        + data.funding_rate[1:]
    )
    return result


def _ewma(values: np.ndarray, span: int) -> float:
    weights = np.exp(np.linspace(-4.0, 0.0, len(values)))
    if len(values) > span:
        values = values[-span:]
        weights = weights[-span:]
    return float(np.average(values, weights=weights))


def build_carry_signal(
    data: CarryData,
    *,
    min_history: int = 180,
    funding_window: int = 30,
    direct_window: int = 24,
    basis_window: int = 90,
    basis_reversion: float = 0.20,
    calibration_window: int = 180,
) -> CarrySignal:
    """Causal reliability-tempered funding + basis-convergence forecast."""
    _validate(data)
    if min_history < 60 or min(funding_window, direct_window, basis_window) < 3:
        raise ValueError("invalid carry signal windows")
    carry = realized_carry(data)
    basis = np.log(data.perp_mark_price / data.spot_price)
    expected = np.zeros(len(data))
    uncertainty = np.zeros(len(data))
    funding_forecast = np.zeros(len(data))
    basis_forecast = np.zeros(len(data))
    weight_track = np.zeros(len(data))
    proxy_track = np.full(len(data), np.nan)
    direct_track = np.full(len(data), np.nan)

    for index in range(min_history, len(data)):
        funding = _ewma(
            data.funding_rate[max(0, index - funding_window + 1) : index + 1],
            funding_window,
        )
        anchor = float(np.median(basis[max(0, index - basis_window + 1) : index + 1]))
        convergence = basis_reversion * float(basis[index] - anchor)
        proxy = funding + convergence
        direct = float(np.mean(carry[index - direct_window + 1 : index + 1]))
        proxy_track[index] = proxy
        direct_track[index] = direct

        calibration_start = max(min_history, index - calibration_window)
        calibration_indices = np.arange(calibration_start, index)
        valid = calibration_indices[
            np.isfinite(proxy_track[calibration_indices])
            & np.isfinite(direct_track[calibration_indices])
        ]
        if len(valid) < 12:
            proxy_weight = 0.5
            predictive_variance = float(np.var(carry[1 : index + 1], ddof=1))
            proxy_bias = 0.0
        else:
            outcomes = carry[valid + 1]
            proxy_errors = proxy_track[valid] - outcomes
            direct_errors = direct_track[valid] - outcomes
            floor = max(float(np.var(outcomes, ddof=1)) * 1e-6, 1e-16)
            proxy_variance = max(float(np.mean(proxy_errors**2)), floor)
            direct_variance = max(float(np.mean(direct_errors**2)), floor)
            proxy_weight = (1 / proxy_variance) / (1 / proxy_variance + 1 / direct_variance)
            predictive_variance = (
                proxy_weight**2 * proxy_variance
                + (1 - proxy_weight) ** 2 * direct_variance
            )
            proxy_bias = float(np.mean(proxy_errors))

        estimate = proxy_weight * (proxy - proxy_bias) + (1 - proxy_weight) * direct
        disagreement = 0.25 * abs((proxy - proxy_bias) - direct)
        effective_count = max(min(len(valid), calibration_window), 12)
        estimation_sd = math.sqrt(predictive_variance / effective_count + disagreement**2)
        expected[index] = estimate
        uncertainty[index] = estimation_sd
        funding_forecast[index] = funding
        basis_forecast[index] = convergence
        weight_track[index] = proxy_weight

    desired = (expected > 0).astype(float)
    desired[:min_history] = 0.0
    return CarrySignal(
        tuple(map(float, desired)),
        tuple(map(float, expected)),
        tuple(map(float, uncertainty)),
        tuple(map(float, funding_forecast)),
        tuple(map(float, basis_forecast)),
        tuple(map(float, weight_track)),
        "RELIABILITY_TEMPERED_FUNDING_PLUS_BASIS_FORECAST",
    )


def _transition_cost(config: Mapping[str, Any]) -> float:
    leg = float(config.get("leg_notional_fraction", 0.5))
    spot = (float(config["spot_fee_bps"]) + float(config["spot_slippage_bps"])) / 10_000
    perp = (float(config["perp_fee_bps"]) + float(config["perp_slippage_bps"])) / 10_000
    return leg * (spot + perp)


def _path_returns(
    carry: np.ndarray,
    positions: Sequence[float],
    *,
    leg_notional_fraction: float,
    transition_cost: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    state = np.asarray(positions, dtype=float)
    gross = np.zeros(len(carry))
    costs = np.zeros(len(carry))
    for index in range(len(carry) - 1):
        gross[index + 1] = state[index] * leg_notional_fraction * carry[index + 1]
        prior = 0.0 if index == 0 else state[index - 1]
        costs[index] += abs(state[index] - prior) * transition_cost
    if len(state) > 1:
        costs[-1] += abs(state[-2]) * transition_cost
    return gross - costs, gross, costs


def _maximum_drawdown(equity: np.ndarray) -> float:
    peaks = np.maximum.accumulate(np.r_[1.0, equity])
    path = np.r_[1.0, equity]
    return float(np.max(1 - path / peaks))


def _metrics(
    net: np.ndarray,
    gross: np.ndarray,
    costs: np.ndarray,
    positions: np.ndarray,
    start: int,
) -> dict[str, Any]:
    values = net[start:]
    gross_values = gross[start:]
    cost_values = costs[start:]
    equity = np.cumprod(1 + values)
    gross_equity = np.cumprod(1 + gross_values)
    volatility = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    sharpe = float(np.mean(values) / volatility * math.sqrt(3 * 365)) if volatility > 0 else 0.0
    evaluated_positions = positions[start - 1 : -1]
    changes = np.abs(np.diff(np.r_[0.0, evaluated_positions]))
    return {
        "events": int(len(values)),
        "net_return": float(equity[-1] - 1),
        "gross_return": float(gross_equity[-1] - 1),
        "cost_drag": float(gross_equity[-1] - equity[-1]),
        "simple_cost_paid": float(np.sum(cost_values)),
        "maximum_drawdown": _maximum_drawdown(equity),
        "annualized_sharpe": sharpe,
        "active_fraction": float(np.mean(evaluated_positions > 0)),
        "position_changes": int(np.sum(changes > 1e-12)),
    }


def run_carry_backtest(data: CarryData, config: Mapping[str, Any]) -> dict[str, Any]:
    _validate(data)
    min_history = int(config.get("min_history", 180))
    if len(data) <= min_history + 30:
        raise ValueError("carry dataset is too short")
    signal = build_carry_signal(
        data,
        min_history=min_history,
        funding_window=int(config.get("funding_window", 30)),
        direct_window=int(config.get("direct_window", 24)),
        basis_window=int(config.get("basis_window", 90)),
        basis_reversion=float(config.get("basis_reversion", 0.20)),
        calibration_window=int(config.get("calibration_window", 180)),
    )
    desired = np.asarray(signal.desired_positions)
    expected = np.asarray(signal.expected_carry)
    uncertainty = np.asarray(signal.estimation_sd)
    leg = float(config.get("leg_notional_fraction", 0.5))
    if not 0 < leg <= 0.5:
        raise ValueError("fully collateralized leg_notional_fraction must be in (0, 0.5]")
    transition_cost = _transition_cost(config)
    execution = control_decision_transaction_execution(
        desired,
        leg * expected,
        leg * uncertainty,
        cost_per_side=transition_cost,
        decision_horizon=int(config.get("decision_horizon", 9)),
        alpha=float(config.get("dtec_alpha", 0.30)),
    )
    full_positions = np.asarray(execution.executed_positions)
    carry = realized_carry(data)
    full_path = _path_returns(
        carry,
        full_positions,
        leg_notional_fraction=leg,
        transition_cost=transition_cost,
    )
    removal_path = _path_returns(
        carry,
        desired,
        leg_notional_fraction=leg,
        transition_cost=transition_cost,
    )
    always_positions = np.zeros(len(data))
    always_positions[min_history:] = 1.0
    always_path = _path_returns(
        carry,
        always_positions,
        leg_notional_fraction=leg,
        transition_cost=transition_cost,
    )
    full = _metrics(*full_path, full_positions, min_history)
    removal = _metrics(*removal_path, desired, min_history)
    always = _metrics(*always_path, always_positions, min_history)
    latest = len(data) - 1
    return {
        "product": "LAB_CRYPTO_MARKET_NEUTRAL_CARRY_V1",
        "mode": "PAPER_RESEARCH_ONLY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "market": {"symbol": data.symbol, "funding_events": len(data)},
        "period": {
            "start_utc": datetime.fromtimestamp(data.timestamp_ms[min_history] / 1000, tz=timezone.utc).isoformat(),
            "end_utc": datetime.fromtimestamp(data.timestamp_ms[-1] / 1000, tz=timezone.utc).isoformat(),
        },
        "data": {"source": data.source, "sha256": data.sha256},
        "protocol": {
            "trade": "long spot + equal-notional short USDT perpetual",
            "leg_notional_fraction": leg,
            "gross_exposure": 2 * leg,
            "net_entry_delta": 0.0,
            "decision_after": "settled funding event t",
            "return_earned": "t to t+1 plus funding settled at t+1",
            "two_leg_transition_cost": transition_cost,
            "close_at_sample_end": True,
            "live_orders": False,
        },
        "lab_composition": {
            "signal": "LMDE/RTE semantics: funding+basis forecast tempered by causal forecast reliability",
            "execution": "V2P033 DTEC two-leg cost and uncertainty gate",
            "attribution": "V2P029 TCEA-style gross/cost/net separation",
        },
        "full_product": full,
        "dtec_removed": removal,
        "always_on_carry": always,
        "dtec_net_return_contribution": full["net_return"] - removal["net_return"],
        "execution_details": execution.to_dict(),
        "latest_paper_signal": {
            "timestamp_utc": datetime.fromtimestamp(data.timestamp_ms[latest] / 1000, tz=timezone.utc).isoformat(),
            "target": "LONG_SPOT_SHORT_PERP" if full_positions[latest] > 0 else "CASH",
            "target_fraction": float(full_positions[latest]),
            "expected_next_carry_per_notional": float(expected[latest]),
            "estimation_sd": float(uncertainty[latest]),
            "current_funding_rate": float(data.funding_rate[latest]),
            "current_basis": float(math.log(data.perp_mark_price[latest] / data.spot_price[latest])),
            "orders_sent": 0,
        },
        "boundary": (
            "Historical mark/open proxies, fixed fees and paper fills only. Borrow, collateral venue risk, "
            "liquidation/ADL, partial fills, latency and tax are not modeled; this is not live-profit evidence."
        ),
    }


def save_carry_paper_signal(
    result: Mapping[str, Any], output: Path, ledger: Path
) -> dict[str, Any]:
    signal = dict(result["latest_paper_signal"])
    previous = None
    if ledger.exists():
        lines = [line for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            previous = float(json.loads(lines[-1])["target_fraction"])
    current = float(signal["target_fraction"])
    if previous is None:
        action = "INITIALIZE_PAPER_BOOK"
    elif current > previous + 1e-12:
        action = "ENTER_PAPER_HEDGE"
    elif current < previous - 1e-12:
        action = "EXIT_PAPER_HEDGE"
    else:
        action = "HOLD"
    leg = float(result["protocol"]["leg_notional_fraction"]) * current
    signal.update(
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "prior_target_fraction": previous,
            "paper_action": action,
            "paper_leg_targets_per_unit_equity": {
                "long_spot_notional": leg,
                "short_perpetual_notional": leg,
            },
            "orders_sent": 0,
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(signal, indent=2), encoding="utf-8")
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(signal, separators=(",", ":")) + "\n")
    return signal


def render_carry_report(result: Mapping[str, Any]) -> str:
    full = result["full_product"]
    removal = result["dtec_removed"]
    always = result["always_on_carry"]
    signal = result["latest_paper_signal"]
    return "\n".join(
        [
            f"# Market-neutral carry - {result['market']['symbol']}",
            "",
            f"Period: {result['period']['start_utc']} to {result['period']['end_utc']}",
            "",
            "| Metric | Lab full | DTEC removed | Always-on carry |",
            "|---|---:|---:|---:|",
            f"| Net return | {100*full['net_return']:.2f}% | {100*removal['net_return']:.2f}% | {100*always['net_return']:.2f}% |",
            f"| Max drawdown | {100*full['maximum_drawdown']:.2f}% | {100*removal['maximum_drawdown']:.2f}% | {100*always['maximum_drawdown']:.2f}% |",
            f"| Annualized Sharpe | {full['annualized_sharpe']:.3f} | {removal['annualized_sharpe']:.3f} | {always['annualized_sharpe']:.3f} |",
            f"| Position changes | {full['position_changes']} | {removal['position_changes']} | {always['position_changes']} |",
            f"| Cost drag | {100*full['cost_drag']:.2f}% | {100*removal['cost_drag']:.2f}% | {100*always['cost_drag']:.2f}% |",
            "",
            f"DTEC contribution versus the same raw signal: **{100*result['dtec_net_return_contribution']:.2f} pp**.",
            f"Latest paper state: **{signal['target']}**; orders sent: **0**.",
            "",
            "## Boundary",
            "",
            result["boundary"],
            "",
        ]
    )
