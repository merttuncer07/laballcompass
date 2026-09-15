from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np

from carry_engine import (
    CarryData,
    _path_returns,
    build_carry_signal,
    load_carry_csv,
    realized_carry,
    run_carry_backtest,
    save_carry_paper_signal,
    save_carry_csv,
    slice_carry_data,
)


def synthetic_carry(count: int = 420) -> CarryData:
    index = np.arange(count, dtype=float)
    spot = 100 * np.exp(0.001 * index)
    basis = 0.002 + 0.0005 * np.sin(index / 12)
    perp = spot * np.exp(basis)
    funding = 0.00012 + 0.00002 * np.sin(index / 17)
    timestamps = np.arange(count, dtype=np.int64) * 28_800_000
    return CarryData(timestamps, spot, perp, funding, "TESTUSDT", "synthetic")


def config() -> dict:
    return {
        "min_history": 120,
        "funding_window": 24,
        "direct_window": 18,
        "basis_window": 60,
        "basis_reversion": 0.20,
        "calibration_window": 120,
        "decision_horizon": 9,
        "dtec_alpha": 0.30,
        "leg_notional_fraction": 0.5,
        "spot_fee_bps": 10,
        "spot_slippage_bps": 2,
        "perp_fee_bps": 5,
        "perp_slippage_bps": 2,
    }


class CarryEngineTests(unittest.TestCase):
    def test_realized_carry_has_funding_and_basis_convergence(self) -> None:
        data = synthetic_carry()
        carry = realized_carry(data)
        expected = data.funding_rate[1] + np.log(data.spot_price[1] / data.spot_price[0]) - np.log(
            data.perp_mark_price[1] / data.perp_mark_price[0]
        )
        self.assertAlmostEqual(carry[1], expected)

    def test_signal_is_prefix_invariant(self) -> None:
        short = build_carry_signal(synthetic_carry(360), min_history=120)
        long = build_carry_signal(synthetic_carry(420), min_history=120)
        np.testing.assert_allclose(short.expected_carry, long.expected_carry[:360])

    def test_two_leg_entry_and_exit_are_both_charged(self) -> None:
        carry = np.zeros(5)
        net, _, cost = _path_returns(
            carry, [0, 1, 1, 1, 1], leg_notional_fraction=0.5, transition_cost=0.001
        )
        self.assertAlmostEqual(float(np.sum(cost)), 0.002)
        self.assertAlmostEqual(float(np.sum(net)), -0.002)

    def test_csv_roundtrip(self) -> None:
        data = synthetic_carry()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "carry.csv"
            save_carry_csv(data, path)
            restored = load_carry_csv(path, data.symbol)
            np.testing.assert_allclose(restored.funding_rate, data.funding_rate)
            self.assertTrue(restored.sha256)

    def test_slice_is_exact(self) -> None:
        data = synthetic_carry()
        sliced = slice_carry_data(data, 20, 320)
        self.assertEqual(len(sliced), 300)
        np.testing.assert_allclose(sliced.spot_price, data.spot_price[20:320])

    def test_result_is_market_neutral_and_paper_only(self) -> None:
        result = run_carry_backtest(synthetic_carry(), config())
        self.assertEqual(result["protocol"]["net_entry_delta"], 0.0)
        self.assertFalse(result["protocol"]["live_orders"])
        self.assertEqual(result["latest_paper_signal"]["orders_sent"], 0)
        self.assertIn("always_on_carry", result)

    def test_paper_ledger_has_equal_opposite_legs_and_no_orders(self) -> None:
        result = run_carry_backtest(synthetic_carry(), config())
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "signal.json"
            ledger = Path(temp) / "ledger.jsonl"
            signal = save_carry_paper_signal(result, output, ledger)
            legs = signal["paper_leg_targets_per_unit_equity"]
            self.assertEqual(legs["long_spot_notional"], legs["short_perpetual_notional"])
            self.assertEqual(signal["orders_sent"], 0)
            self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
