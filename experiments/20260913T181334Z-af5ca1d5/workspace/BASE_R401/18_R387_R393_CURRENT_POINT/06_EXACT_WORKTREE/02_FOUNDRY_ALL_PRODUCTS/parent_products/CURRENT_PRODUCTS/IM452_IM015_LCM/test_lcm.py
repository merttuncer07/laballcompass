from __future__ import annotations

import unittest

from lcm import Claim, FundingChannel, LiquidityConversionMap


class LiquidityConversionMapTests(unittest.TestCase):
    def test_nominal_is_not_deployable(self) -> None:
        model = LiquidityConversionMap(
            [Claim("c", 100, "a", "receivable", "none", False)],
            [FundingChannel("f", 100, ("verified",), ("receivable",), 0.8)],
        )
        result = model.solve()
        self.assertEqual(result["nominal_resource"], 100)
        self.assertEqual(result["deployable_liquidity"], 0)

    def test_capacity_and_anchor_limits_hold(self) -> None:
        model = LiquidityConversionMap(
            [
                Claim("c1", 100, "anchor", "receivable", "v", True),
                Claim("c2", 100, "anchor", "receivable", "v", True),
            ],
            [FundingChannel("f", 100, ("v",), ("receivable",), 1.0, 0.5)],
        )
        result = model.solve()
        self.assertAlmostEqual(result["deployable_liquidity"], 50.0)

    def test_verification_has_measurable_marginal_value(self) -> None:
        model = LiquidityConversionMap(
            [Claim("c", 100, "a", "receivable", "none", False)],
            [FundingChannel("f", 100, ("v",), ("receivable",), 0.8)],
        )
        value = model.marginal_verification_value("c", "v")
        self.assertAlmostEqual(value["marginal_deployable_liquidity"], 80.0)


if __name__ == "__main__":
    unittest.main()
