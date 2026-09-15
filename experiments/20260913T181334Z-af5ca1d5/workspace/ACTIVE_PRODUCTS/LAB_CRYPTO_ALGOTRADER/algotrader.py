"""Paper-first spot crypto algotrader produced from Lab mechanisms."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping
import urllib.parse
import urllib.request

import numpy as np

from lab_mechanisms import (
    allocate_core_satellite_exposure,
    build_lab_memory_decision_positions,
    control_decision_transaction_execution,
)


INTERVAL_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}
FIELDS = ("open_time_ms", "close_time_ms", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class CandleData:
    open_time_ms: np.ndarray
    close_time_ms: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    source: str
    sha256: str

    def __len__(self) -> int:
        return len(self.close)


@dataclass(frozen=True)
class PathResult:
    positions: np.ndarray
    net_returns: np.ndarray
    gross_returns: np.ndarray
    cost_paid: np.ndarray
    execution: dict[str, Any]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate(data: CandleData) -> None:
    lengths = {len(getattr(data, field)) for field in FIELDS}
    if len(lengths) != 1 or next(iter(lengths), 0) < 100:
        raise ValueError("aligned candle columns with at least 100 rows required")
    for field in FIELDS:
        values = np.asarray(getattr(data, field))
        if values.ndim != 1 or np.any(~np.isfinite(values.astype(float))):
            raise ValueError(f"{field} must be a finite vector")
    if np.any(np.diff(data.open_time_ms) <= 0):
        raise ValueError("open timestamps must increase strictly")
    if np.any(data.close_time_ms < data.open_time_ms):
        raise ValueError("close time precedes open time")
    if any(np.any(getattr(data, field) <= 0) for field in ("open", "high", "low", "close")):
        raise ValueError("OHLC prices must be positive")
    if np.any(data.volume < 0):
        raise ValueError("volume must be non-negative")
    if np.any(data.low > np.minimum(data.open, data.close)) or np.any(
        data.high < np.maximum(data.open, data.close)
    ):
        raise ValueError("OHLC geometry is inconsistent")


def fetch_closed_klines(
    symbol: str,
    interval: str,
    bars: int,
    *,
    base_url: str = "https://data-api.binance.vision",
    timeout_seconds: int = 20,
) -> CandleData:
    if interval not in INTERVAL_MINUTES:
        raise ValueError(f"unsupported interval: {interval}")
    if bars < 100 or bars > 20_000:
        raise ValueError("bars must be between 100 and 20000")
    symbol = symbol.upper()
    rows: list[list[Any]] = []
    end_time = int(time.time() * 1000)
    while len(rows) < bars + 2:
        limit = min(1000, bars + 2 - len(rows))
        query = urllib.parse.urlencode(
            {"symbol": symbol, "interval": interval, "limit": limit, "endTime": end_time}
        )
        request = urllib.request.Request(
            f"{base_url}/api/v3/klines?{query}",
            headers={"User-Agent": "Lab-Crypto-Algotrader/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            page = json.loads(response.read().decode("utf-8"))
        if not isinstance(page, list) or not page:
            break
        rows = page + rows
        end_time = int(page[0][0]) - 1
        if len(page) < limit:
            break
        time.sleep(0.05)
    unique = {int(row[0]): row for row in rows}
    now_ms = int(time.time() * 1000)
    closed = [unique[key] for key in sorted(unique) if int(unique[key][6]) < now_ms]
    if len(closed) < bars:
        raise RuntimeError(f"only {len(closed)} closed candles returned; requested {bars}")
    selected = closed[-bars:]
    arrays = {
        "open_time_ms": np.asarray([int(row[0]) for row in selected], dtype=np.int64),
        "close_time_ms": np.asarray([int(row[6]) for row in selected], dtype=np.int64),
        "open": np.asarray([float(row[1]) for row in selected]),
        "high": np.asarray([float(row[2]) for row in selected]),
        "low": np.asarray([float(row[3]) for row in selected]),
        "close": np.asarray([float(row[4]) for row in selected]),
        "volume": np.asarray([float(row[5]) for row in selected]),
    }
    data = CandleData(**arrays, source=f"{base_url}/api/v3/klines:{symbol}:{interval}", sha256="")
    _validate(data)
    return data


def save_csv(data: CandleData, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        for row in zip(*(getattr(data, field) for field in FIELDS)):
            writer.writerow(row)


def load_csv(path: Path) -> CandleData:
    source = path.resolve()
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    arrays: dict[str, np.ndarray] = {}
    for field in FIELDS:
        if not rows or field not in rows[0]:
            raise ValueError(f"missing CSV column: {field}")
        dtype = np.int64 if field.endswith("_ms") else float
        arrays[field] = np.asarray([dtype(row[field]) for row in rows], dtype=dtype)
    data = CandleData(**arrays, source=str(source), sha256=_sha256(source))
    _validate(data)
    return data


def slice_data(data: CandleData, start: int, stop: int) -> CandleData:
    if not 0 <= start < stop <= len(data):
        raise ValueError("invalid candle slice")
    arrays = {field: np.asarray(getattr(data, field)[start:stop]).copy() for field in FIELDS}
    sliced = CandleData(
        **arrays,
        source=f"{data.source}#rows={start}:{stop}",
        sha256=data.sha256,
    )
    _validate(sliced)
    return sliced


def _maximum_drawdown(equity: np.ndarray) -> float:
    if not len(equity):
        return 0.0
    peak = np.maximum.accumulate(equity)
    return float(np.max(1.0 - equity / peak))


def _annualized_sharpe(returns: np.ndarray, interval_minutes: int) -> float:
    if len(returns) < 2 or float(np.std(returns, ddof=1)) <= 0:
        return 0.0
    bars_per_year = 365 * 24 * 60 / interval_minutes
    return float(np.mean(returns) / np.std(returns, ddof=1) * math.sqrt(bars_per_year))


def _risk_targets(
    close: np.ndarray,
    raw_positions: np.ndarray,
    *,
    interval_minutes: int,
    annual_volatility_target: float,
) -> np.ndarray:
    close_returns = np.zeros(len(close))
    close_returns[1:] = np.diff(np.log(close))
    bars_per_year = 365 * 24 * 60 / interval_minutes
    targets = np.zeros(len(close))
    for index in range(len(close)):
        trailing = close_returns[max(1, index - 96) : index]
        realized = (
            float(np.std(trailing, ddof=1) * math.sqrt(bars_per_year))
            if len(trailing) >= 24
            else annual_volatility_target
        )
        scale = min(1.0, annual_volatility_target / realized) if realized > 0 else 0.0
        targets[index] = raw_positions[index] * scale
    return targets


def _execute_next_open(
    opens: np.ndarray,
    targets: np.ndarray,
    *,
    cost_per_side: float,
    maximum_drawdown: float,
    cooldown_bars: int,
) -> PathResult:
    execution_returns = np.zeros(len(opens))
    execution_returns[:-2] = opens[2:] / opens[1:-1] - 1
    positions = np.zeros(len(opens))
    gross = np.zeros(len(opens))
    costs = np.zeros(len(opens))
    net = np.zeros(len(opens))
    equity = peak = 1.0
    cooldown = 0
    prior = 0.0
    triggered = 0
    realized_stop = len(opens) - 2
    for index in range(realized_stop):
        in_cooldown = cooldown > 0
        requested = 0.0 if in_cooldown else float(targets[index])
        turnover = abs(requested - prior)
        gross[index] = requested * execution_returns[index]
        costs[index] = turnover * cost_per_side
        net[index] = gross[index] - costs[index]
        equity *= 1 + net[index]
        peak = max(peak, equity)
        if in_cooldown:
            cooldown -= 1
            if cooldown == 0:
                peak = equity
        elif 1 - equity / peak >= maximum_drawdown:
            # The triggering loss remains realized. Cash starts next executable bar.
            cooldown = cooldown_bars
            peak = equity
            triggered += 1
        positions[index] = requested
        prior = requested
    positions[realized_stop:] = 0.0 if cooldown > 0 else targets[realized_stop:]
    return PathResult(
        positions,
        net,
        gross,
        costs,
        {"drawdown_cooldowns": triggered, "cooldown_active_at_end": cooldown > 0},
    )


def build_path(
    data: CandleData,
    config: Mapping[str, Any],
    *,
    use_dtec: bool,
    use_core_satellite: bool = False,
) -> tuple[PathResult, dict]:
    interval = str(config["interval"])
    interval_minutes = INTERVAL_MINUTES[interval]
    train_bars = int(config["train_bars"])
    lmde = build_lab_memory_decision_positions(
        data.close,
        train_bars=train_bars,
        test_bars=int(config["refit_bars"]),
        purge_bars=int(config.get("purge_bars", 2)),
        max_lag=int(config["max_lag"]),
        decision_alpha=float(config["lmde_alpha"]),
        direct_window=int(config["direct_window"]),
    )
    raw = np.asarray(lmde.positions)
    expected = np.asarray(lmde.expected_next_returns)
    uncertainty = np.asarray(lmde.aggregate_estimation_sd)
    core = None
    if use_core_satellite:
        core = allocate_core_satellite_exposure(
            data.close,
            raw,
            fast_window=int(config.get("core_fast_window", 64)),
            slow_window=int(config.get("core_slow_window", 256)),
            core_position=float(config.get("core_position", 1.0)),
        )
        raw = np.asarray(core.combined_positions)
    risk_targets = _risk_targets(
        data.close,
        raw,
        interval_minutes=interval_minutes,
        annual_volatility_target=float(config["annual_volatility_target"]),
    )
    cost_per_side = (float(config["fee_bps"]) + float(config["slippage_bps"])) / 10_000
    execution = None
    if use_dtec:
        execution = control_decision_transaction_execution(
            risk_targets,
            expected,
            uncertainty,
            cost_per_side=cost_per_side,
            decision_horizon=int(config["dtec_horizon"]),
            alpha=float(config["dtec_alpha"]),
        )
        targets = np.asarray(execution.executed_positions)
    else:
        targets = risk_targets
    path = _execute_next_open(
        data.open,
        targets,
        cost_per_side=cost_per_side,
        maximum_drawdown=float(config["maximum_drawdown"]),
        cooldown_bars=int(config["cooldown_bars"]),
    )
    details = {
        "lmde": {
            "active_fraction": lmde.active_fraction,
            "mean_position": lmde.mean_position,
            "blocks": list(lmde.block_diagnostics),
        },
        "dtec": None if execution is None else execution.to_dict(),
        "core_satellite": None if core is None else core.to_dict(),
    }
    return path, details


def _path_metrics(data: CandleData, config: Mapping[str, Any], path: PathResult) -> dict[str, Any]:
    start = int(config["train_bars"])
    stop = len(data) - 2
    net = path.net_returns[start:stop]
    gross = path.gross_returns[start:stop]
    costs = path.cost_paid[start:stop]
    positions = path.positions[start:stop]
    equity = np.cumprod(1 + net)
    gross_equity = np.cumprod(1 + gross)
    benchmark_prices = data.open[start + 1 :]
    benchmark_equity = benchmark_prices / benchmark_prices[0]
    turnover = np.abs(np.diff(np.r_[0.0, positions]))
    return {
        "evaluated_bars": len(net),
        "start_utc": datetime.fromtimestamp(
            data.open_time_ms[start + 1] / 1000, tz=timezone.utc
        ).isoformat(),
        "end_utc": datetime.fromtimestamp(data.open_time_ms[-1] / 1000, tz=timezone.utc).isoformat(),
        "net_return": float(equity[-1] - 1),
        "gross_return": float(gross_equity[-1] - 1),
        "cost_drag": float(gross_equity[-1] - equity[-1]),
        "simple_cost_paid": float(np.sum(costs)),
        "maximum_drawdown": _maximum_drawdown(equity),
        "annualized_sharpe": _annualized_sharpe(net, INTERVAL_MINUTES[str(config["interval"])]),
        "buy_hold_return": float(benchmark_equity[-1] - 1),
        "buy_hold_maximum_drawdown": _maximum_drawdown(benchmark_equity),
        "turnover": float(np.sum(turnover)),
        "position_changes": int(np.sum(turnover > 1e-9)),
        "average_exposure": float(np.mean(positions)),
        "cash_fraction": float(np.mean(positions <= 1e-12)),
        **path.execution,
    }


def run_research_backtest(data: CandleData, config: Mapping[str, Any]) -> dict[str, Any]:
    _validate(data)
    if len(data) <= int(config["train_bars"]) + int(config["refit_bars"]):
        raise ValueError("dataset is too short for train_bars + refit_bars")
    full_path, details = build_path(data, config, use_dtec=True)
    removal_path, removal_details = build_path(data, config, use_dtec=False)
    full = _path_metrics(data, config, full_path)
    removal = _path_metrics(data, config, removal_path)
    contribution = full["net_return"] - removal["net_return"]
    return {
        "product": "LAB_CRYPTO_ALGOTRADER_V1",
        "mode": "RESEARCH_BACKTEST",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "market": {"symbol": config["symbol"], "interval": config["interval"], "bars": len(data)},
        "data": {"source": data.source, "sha256": data.sha256},
        "protocol": {
            "signal_after": "close[t]",
            "fill_at": "open[t+1]",
            "return_earned": "open[t+1] to open[t+2]",
            "cost_per_side": (float(config["fee_bps"]) + float(config["slippage_bps"])) / 10_000,
            "long_cash_spot_only": True,
            "live_orders": False,
        },
        "lab_composition": {
            "full": "V2P032_LMDE -> V2P033_DTEC -> causal risk shell",
            "removal": "V2P032_LMDE -> causal risk shell (DTEC removed)",
        },
        "full_product": full,
        "dtec_removal": removal,
        "dtec_net_return_contribution": contribution,
        "dtec_contributes_on_this_sample": contribution > 0,
        "mechanism_details": details,
        "removal_details": removal_details,
        "paper_signal": {
            "last_closed_candle_utc": datetime.fromtimestamp(
                data.close_time_ms[-1] / 1000, tz=timezone.utc
            ).isoformat(),
            "last_close": float(data.close[-1]),
            "target_spot_exposure": float(full_path.positions[-1]),
            "meaning": "0=cash, 1=fully long spot; fractional values are risk-scaled exposure",
        },
        "boundary": "Historical paper evidence only. No future return or live-profit claim.",
    }


def save_paper_signal(result: Mapping[str, Any], output: Path, ledger: Path) -> dict[str, Any]:
    signal = dict(result["paper_signal"])
    prior_exposure = None
    if ledger.exists():
        lines = [line for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            prior_exposure = float(json.loads(lines[-1])["target_spot_exposure"])
    current = float(signal["target_spot_exposure"])
    if prior_exposure is None:
        action = "INITIALIZE"
    elif current > prior_exposure + 1e-9:
        action = "INCREASE_PAPER_EXPOSURE"
    elif current < prior_exposure - 1e-9:
        action = "DECREASE_PAPER_EXPOSURE"
    else:
        action = "HOLD"
    signal.update(
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "prior_paper_exposure": prior_exposure,
            "paper_action": action,
            "orders_sent": 0,
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(signal, indent=2), encoding="utf-8")
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(signal, separators=(",", ":")) + "\n")
    return signal


def render_report(result: Mapping[str, Any]) -> str:
    full = result["full_product"]
    removal = result["dtec_removal"]
    signal = result["paper_signal"]
    return "\n".join(
        [
            f"# Lab Crypto Algotrader — {result['market']['symbol']} {result['market']['interval']}",
            "",
            "## Frozen walk-forward result",
            "",
            "| Metric | Full Lab product | DTEC removed |",
            "|---|---:|---:|",
            f"| Net return | {100 * full['net_return']:.2f}% | {100 * removal['net_return']:.2f}% |",
            f"| Maximum drawdown | {100 * full['maximum_drawdown']:.2f}% | {100 * removal['maximum_drawdown']:.2f}% |",
            f"| Annualized Sharpe | {full['annualized_sharpe']:.3f} | {removal['annualized_sharpe']:.3f} |",
            f"| Position changes | {full['position_changes']} | {removal['position_changes']} |",
            f"| Cost drag | {100 * full['cost_drag']:.2f}% | {100 * removal['cost_drag']:.2f}% |",
            "",
            f"Buy-and-hold return over the evaluated path: **{100 * full['buy_hold_return']:.2f}%**.  ",
            f"DTEC contribution on this sample: **{100 * result['dtec_net_return_contribution']:.2f} percentage points**.  ",
            f"Latest paper target exposure: **{100 * signal['target_spot_exposure']:.1f}%**.",
            "",
            "## Interpretation",
            "",
            "The full product is LMDE → DTEC with causal next-open execution, volatility sizing, "
            "transaction costs and a drawdown cooldown. DTEC is also removed and rerun on the same "
            "sample; a negative contribution means the full composition is not supported there.",
            "",
            "## Boundary",
            "",
            result["boundary"],
            "The program never submits an exchange order.",
            "",
        ]
    )
