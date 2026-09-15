import unittest

from mcpr import Offer, clear_uniform_price_market


class MCPRTests(unittest.TestCase):
    def setUp(self) -> None:
        self.offers = [Offer("low", 50.0, 10.0), Offer("mid", 50.0, 30.0), Offer("high", 50.0, 60.0)]

    def test_marginal_offer_sets_common_price_and_rent(self) -> None:
        result = clear_uniform_price_market(self.offers, 80.0)
        self.assertEqual(result.clearing_price, 30.0)
        self.assertAlmostEqual(result.total_inframarginal_rent, 1000.0)
        self.assertAlmostEqual(result.served_quantity, 80.0)

    def test_equal_price_marginal_block_is_prorated(self) -> None:
        result = clear_uniform_price_market(
            [Offer("base", 20, 5), Offer("a", 40, 20), Offer("b", 60, 20)], 70
        )
        rows = {row.name: row for row in result.dispatch}
        self.assertAlmostEqual(rows["a"].dispatched_quantity, 20.0)
        self.assertAlmostEqual(rows["b"].dispatched_quantity, 30.0)

    def test_shortage_uses_explicit_scarcity_price(self) -> None:
        result = clear_uniform_price_market(self.offers, 200.0, scarcity_price=500.0)
        self.assertEqual(result.status, "SHORTAGE")
        self.assertEqual(result.unserved_quantity, 50.0)
        self.assertEqual(result.clearing_price, 500.0)

    def test_zero_demand_has_no_price(self) -> None:
        result = clear_uniform_price_market(self.offers, 0.0)
        self.assertEqual(result.status, "NO_DEMAND")
        self.assertIsNone(result.clearing_price)


if __name__ == "__main__":
    unittest.main()
