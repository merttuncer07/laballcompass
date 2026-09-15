from __future__ import annotations

import json
from pathlib import Path

from lcm import Claim, FundingChannel, LiquidityConversionMap


def build_map() -> LiquidityConversionMap:
    return LiquidityConversionMap(
        [
            Claim("C1", 300_000, "MegaBuyer", "receivable", "buyer_approved", True),
            Claim("C2", 250_000, "MegaBuyer", "receivable", "buyer_approved", True),
            Claim("C3", 200_000, "OtherBuyer", "receivable", "independent_audit", True),
            Claim("C4", 180_000, "OtherBuyer", "receivable", "none", False),
            Claim("C5", 150_000, "MegaBuyer", "inventory", "warehouse", True),
        ],
        [
            FundingChannel(
                "BankA", 350_000, ("buyer_approved", "independent_audit"), ("receivable",), 0.85, 0.60
            ),
            FundingChannel(
                "BankB", 250_000, ("independent_audit", "warehouse"), ("receivable", "inventory"), 0.75, 0.70
            ),
            FundingChannel(
                "Fintech", 200_000, ("buyer_approved",), ("receivable",), 0.65, 0.50
            ),
        ],
    )


if __name__ == "__main__":
    liquidity_map = build_map()
    result = {
        "current": liquidity_map.solve(0),
        "verify_C4_with_independent_audit": liquidity_map.marginal_verification_value(
            "C4", "independent_audit", 0
        ),
    }
    output = Path(__file__).with_name("liquidity_conversion_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
