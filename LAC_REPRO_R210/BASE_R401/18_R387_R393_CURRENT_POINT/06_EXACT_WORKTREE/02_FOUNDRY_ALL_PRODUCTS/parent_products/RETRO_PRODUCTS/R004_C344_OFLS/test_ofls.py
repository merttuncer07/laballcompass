import unittest

from ofls import simulate_redemption


BASE = dict(fund_units=1000, nav_per_unit=100, cash_buffer=5000, requested_units=300,
            liquidatable_asset_book_value=95000, linear_sale_cost=0.02, market_impact=0.20)


class OFLSTests(unittest.TestCase):
    def test_ordinary_nav_leaves_sale_cost_to_remaining_holders(self):
        result = simulate_redemption(**BASE)
        self.assertGreater(result.cost_left_to_remaining_holders, 0)
        self.assertGreater(result.remaining_nav_dilution, 0)

    def test_full_swing_internalizes_actual_cost(self):
        result = simulate_redemption(**BASE, swing_capture_fraction=1.0)
        self.assertAlmostEqual(result.cost_left_to_remaining_holders, 0.0, places=8)
        self.assertAlmostEqual(result.remaining_nav_per_unit, 100.0, places=8)

    def test_gate_defers_units_and_reduces_forced_sale(self):
        open_result = simulate_redemption(**BASE)
        gated = simulate_redemption(**BASE, gate_fraction=0.1)
        self.assertEqual(gated.served_units, 100)
        self.assertEqual(gated.deferred_units, 200)
        self.assertLess(gated.forced_sale_cost, open_result.forced_sale_cost)

    def test_unfundable_redemption_is_explicit(self):
        with self.assertRaises(ValueError):
            simulate_redemption(**{**BASE, "liquidatable_asset_book_value": 10000})


if __name__ == "__main__": unittest.main()
