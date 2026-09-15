"""Open-Fund Liquidity and Swing-pricing simulator (OFLS) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import brentq


@dataclass(frozen=True)
class RedemptionScenario:
    requested_units: float
    served_units: float
    deferred_units: float
    gross_nav_claim: float
    cash_paid_to_redeemers: float
    swing_charge: float
    assets_sold_at_book_value: float
    forced_sale_cost: float
    cost_borne_by_redeemers: float
    cost_left_to_remaining_holders: float
    first_mover_advantage_per_served_unit: float
    remaining_units: float
    remaining_nav_per_unit: float
    remaining_nav_dilution: float
    gate_fraction: float
    swing_capture_fraction: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_redemption(
    *,
    fund_units: float,
    nav_per_unit: float,
    cash_buffer: float,
    requested_units: float,
    liquidatable_asset_book_value: float,
    linear_sale_cost: float,
    market_impact: float,
    gate_fraction: float = 1.0,
    swing_capture_fraction: float = 0.0,
) -> RedemptionScenario:
    """Simulate one redemption window with a gate and endogenous swing charge."""

    numbers = [fund_units, nav_per_unit, cash_buffer, requested_units, liquidatable_asset_book_value,
               linear_sale_cost, market_impact, gate_fraction, swing_capture_fraction]
    if not all(np.isfinite(numbers)):
        raise ValueError("all inputs must be finite")
    if fund_units <= 0 or nav_per_unit <= 0 or cash_buffer < 0 or requested_units < 0 or liquidatable_asset_book_value <= 0:
        raise ValueError("units/NAV/liquid assets must be positive and cash/request non-negative")
    if requested_units > fund_units or not 0 < gate_fraction <= 1 or not 0 <= swing_capture_fraction <= 1:
        raise ValueError("request cannot exceed units; gate in (0,1], swing capture in [0,1]")
    if linear_sale_cost < 0 or market_impact < 0 or linear_sale_cost + 2 * market_impact >= 1:
        raise ValueError("sale-cost parameters must keep net proceeds increasing over liquidatable assets")
    total_assets = fund_units * nav_per_unit
    if cash_buffer + liquidatable_asset_book_value > total_assets + 1e-9:
        raise ValueError("cash plus liquidatable book value cannot exceed total fund assets")

    served = min(requested_units, gate_fraction * fund_units)
    gross = served * nav_per_unit

    def sale_for_payout(payout: float) -> tuple[float, float]:
        need = max(0.0, payout - cash_buffer)
        if need == 0:
            return 0.0, 0.0
        def net(book: float) -> float:
            return (1 - linear_sale_cost) * book - market_impact * book**2 / liquidatable_asset_book_value
        capacity = net(liquidatable_asset_book_value)
        if need > capacity + 1e-9:
            raise ValueError("redemption cannot be funded from declared cash and liquidatable assets")
        book = brentq(lambda value: net(value) - need, 0.0, liquidatable_asset_book_value)
        return float(book), float(book - need)

    if swing_capture_fraction == 0 or gross <= cash_buffer:
        payout = gross
    else:
        def fixed_point(payout: float) -> float:
            _, cost = sale_for_payout(payout)
            return payout - (gross - swing_capture_fraction * cost)
        payout = float(brentq(fixed_point, 0.0, gross))
    sold, sale_cost = sale_for_payout(payout)
    swing_charge = gross - payout
    remaining_units = fund_units - served
    remaining_assets = total_assets - payout - sale_cost
    remaining_nav = remaining_assets / remaining_units if remaining_units > 0 else 0.0
    left_cost = max(0.0, sale_cost - swing_charge)
    dilution = max(0.0, nav_per_unit - remaining_nav) if remaining_units else 0.0
    return RedemptionScenario(
        requested_units, float(served), float(requested_units - served), float(gross), payout,
        float(swing_charge), sold, sale_cost, float(swing_charge), left_cost,
        float(left_cost / served) if served else 0.0, float(remaining_units), float(remaining_nav),
        float(dilution), float(gate_fraction), float(swing_capture_fraction), "FUNDED",
    )
