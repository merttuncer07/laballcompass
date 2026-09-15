from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from algotrader import (
    CandleData,
    _execute_next_open,
    load_csv,
    run_research_backtest,
    save_csv,
    save_paper_signal,
    slice_data,
)
from lab_mechanisms import (
    allocate_core_satellite_exposure,
    build_lab_memory_decision_positions,
    control_decision_transaction_execution,
)
from validate_markets import summarize
from validate_time_windows import build_windows, summarize_windows


def synthetic_data(count: int = 420) -> CandleData:
    index = np.arange(count, dtype=float)
    close = 100 * np.exp(0.00035 * index + 0.025 * np.sin(index / 13))
    open_price = close * (1 + 0.001 * np.sin(index / 5))
    high = np.maximum(open_price, close) * 1.003
    low = np.minimum(open_price, close) * 0.997
    timestamps = np.arange(count, dtype=np.int64) * 3_600_000
    return CandleData(
        timestamps,
        timestamps + 3_599_999,
        open_price,
        high,
        low,
        close,
        np.full(count, 1000.0),
        "synthetic",
        "synthetic",
    )


def config() -> dict:
    return {
        "symbol": "TESTUSDT",
        "interval": "1h",
        "train_bars": 220,
        "refit_bars": 50,
        "purge_bars": 2,
        "max_lag": 3,
        "lmde_alpha": 0.30,
        "direct_window": 10,
        "dtec_horizon": 8,
        "dtec_alpha": 0.20,
        "annual_volatility_target": 0.20,
        "maximum_drawdown": 0.07,
        "cooldown_bars": 24,
        "fee_bps": 10,
        "slippage_bps": 2,
    }


class LabCryptoAlgotraderTests(unittest.TestCase):
    def test_lmde_is_prefix_invariant_for_completed_blocks(self) -> None:
        data = synthetic_data(470)
        short = build_lab_memory_decision_positions(
            data.close[:420], train_bars=220, test_bars=50, max_lag=3, direct_window=10
        )
        long = build_lab_memory_decision_positions(
            data.close, train_bars=220, test_bars=50, max_lag=3, direct_window=10
        )
        np.testing.assert_allclose(short.positions[:400], long.positions[:400])

    def test_dtec_avoids_turnover(self) -> None:
        desired = [0, 0.5, 0, 0.5, 0, 0.5]
        result = control_decision_transaction_execution(
            desired,
            [0, 0.0001, -0.0001, 0.0001, -0.0001, 0.0001],
            [0, 0.01, 0.01, 0.01, 0.01, 0.01],
            cost_per_side=0.0012,
        )
        self.assertGreater(result.avoided_turnover, 0)

    def test_core_satellite_uses_only_slow_bull_state(self) -> None:
        close = np.linspace(100, 200, 400)
        tactical = np.zeros(400)
        result = allocate_core_satellite_exposure(close, tactical)
        positions = np.asarray(result.combined_positions)
        self.assertTrue(np.all(positions[:255] == 0))
        self.assertTrue(np.all(positions[255:] == 1))

    def test_next_open_cost_reduces_return(self) -> None:
        opens = np.asarray([100, 101, 102, 103, 104, 105], dtype=float)
        targets = np.ones(6)
        free = _execute_next_open(opens, targets, cost_per_side=0, maximum_drawdown=1, cooldown_bars=1)
        costly = _execute_next_open(opens, targets, cost_per_side=0.01, maximum_drawdown=1, cooldown_bars=1)
        self.assertGreater(np.prod(1 + free.net_returns), np.prod(1 + costly.net_returns))

    def test_drawdown_triggering_loss_is_not_erased(self) -> None:
        opens = np.asarray([100, 100, 100, 80, 80, 80], dtype=float)
        path = _execute_next_open(
            opens, np.ones(6), cost_per_side=0, maximum_drawdown=0.05, cooldown_bars=2
        )
        self.assertLess(path.net_returns[1], -0.1)
        self.assertEqual(path.execution["drawdown_cooldowns"], 1)

    def test_csv_roundtrip(self) -> None:
        data = synthetic_data()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candles.csv"
            save_csv(data, path)
            restored = load_csv(path)
            np.testing.assert_allclose(data.close, restored.close)
            self.assertNotEqual(restored.sha256, "")

    def test_slice_preserves_only_declared_rows(self) -> None:
        data = synthetic_data()
        sliced = slice_data(data, 20, 220)
        self.assertEqual(len(sliced), 200)
        np.testing.assert_allclose(sliced.close, data.close[20:220])

    def test_research_result_contains_removal_comparator(self) -> None:
        result = run_research_backtest(synthetic_data(), config())
        self.assertEqual(result["product"], "LAB_CRYPTO_ALGOTRADER_V1")
        self.assertIn("dtec_removal", result)
        self.assertFalse(result["protocol"]["live_orders"])

    def test_paper_signal_never_sends_orders(self) -> None:
        result = run_research_backtest(synthetic_data(), config())
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "signal.json"
            ledger = Path(temp) / "ledger.jsonl"
            signal = save_paper_signal(result, output, ledger)
            self.assertEqual(signal["orders_sent"], 0)
            self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["orders_sent"], 0)

    def test_cross_market_summary_does_not_hide_negative_market(self) -> None:
        first = run_research_backtest(synthetic_data(), config())
        second = json.loads(json.dumps(first))
        second["market"]["symbol"] = "OTHERUSDT"
        second["full_product"]["net_return"] = -0.25
        second["full_product"]["maximum_drawdown"] = 0.30
        summary = summarize([first, second])
        self.assertEqual(summary["aggregate"]["market_count"], 2)
        self.assertEqual(summary["aggregate"]["worst_net_return"], -0.25)
        self.assertEqual(summary["aggregate"]["worst_maximum_drawdown"], 0.30)

    def test_chronological_windows_include_latest_tail(self) -> None:
        windows = build_windows(10000, 3500, 2000)
        self.assertEqual(windows[-1], (6500, 10000))
        rows = [
            {
                "symbol": "BTCUSDT",
                "net_return": 0.1,
                "maximum_drawdown": 0.05,
                "buy_hold_return": 0.2,
                "dtec_contribution": 0.03,
            },
            {
                "symbol": "BTCUSDT",
                "net_return": -0.2,
                "maximum_drawdown": 0.25,
                "buy_hold_return": -0.1,
                "dtec_contribution": -0.02,
            },
        ]
        summary = summarize_windows(rows)
        self.assertEqual(summary["aggregate"]["positive_window_count"], 1)
        self.assertEqual(summary["aggregate"]["worst_net_return"], -0.2)


if __name__ == "__main__":
    unittest.main()
