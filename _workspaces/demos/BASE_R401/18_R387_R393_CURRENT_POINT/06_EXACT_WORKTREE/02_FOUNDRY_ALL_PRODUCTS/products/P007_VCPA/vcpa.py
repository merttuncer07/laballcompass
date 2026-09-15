"""Verified-Claim Capital Priority Auction (VCPA) v0.1.

LCM -> residual funding quantity -> MCPR capital-supply auction -> explicit
rate adapter -> PRIU priority audit.

Adapter contract: MCPR Offer.price is interpreted here as a non-negative
one-period simple required return rate (e.g. 0.10 == 10%).
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Sequence
import math

if __package__:
    from .parents.lcm import Claim as LiquidityClaim, FundingChannel, LiquidityConversionMap
else:
    from parents.lcm import Claim as LiquidityClaim, FundingChannel, LiquidityConversionMap
if __package__:
    from .parents.mcpr import Offer, MarketClear, clear_uniform_price_market
else:
    from parents.mcpr import Offer, MarketClear, clear_uniform_price_market
if __package__:
    from .parents.priu import Claim as LiabilityClaim, Scenario, PriorityResetAudit, audit_priority_reset
else:
    from parents.priu import Claim as LiabilityClaim, Scenario, PriorityResetAudit, audit_priority_reset

@dataclass(frozen=True)
class CapitalPriorityPlan:
    funding_need: float
    deployable_verified_liquidity: float
    residual_capital_demand: float
    market_clear: MarketClear | None
    clearing_required_return: float | None
    priority_audit: PriorityResetAudit | None
    financing_complete: bool
    protected_financing_available: bool
    status: str
    def to_dict(self): return asdict(self)


def clear_verified_capital_plan(
    *, funding_need: float, liquidity_claims: Sequence[LiquidityClaim], funding_channels: Sequence[FundingChannel],
    capital_offers: Sequence[Offer], existing_liability_claims: Sequence[LiabilityClaim], scenarios: Sequence[Scenario],
    horizon_days: int = 0, scarcity_rate: float | None = None,
) -> CapitalPriorityPlan:
    if not math.isfinite(funding_need) or funding_need < 0:
        raise ValueError("funding_need must be finite and non-negative")
    if any((not math.isfinite(o.price)) or o.price < 0 for o in capital_offers):
        raise ValueError("VCPA requires non-negative finite offer prices interpreted as simple return rates")
    if scarcity_rate is not None and (not math.isfinite(scarcity_rate) or scarcity_rate < 0):
        raise ValueError("scarcity_rate must be non-negative and finite")
    liquidity=LiquidityConversionMap(liquidity_claims,funding_channels).solve(horizon_days=horizon_days)
    deployable=float(liquidity['deployable_liquidity'])
    residual=max(0.0,funding_need-min(funding_need,deployable))
    if residual <= 1e-12:
        return CapitalPriorityPlan(funding_need,deployable,0.0,None,None,None,True,True,'VERIFIED_LIQUIDITY_FULLY_COVERS_NEED')
    market=clear_uniform_price_market(capital_offers,residual,scarcity_price=scarcity_rate)
    if market.unserved_quantity > 1e-10 or market.clearing_price is None:
        return CapitalPriorityPlan(funding_need,deployable,residual,market,market.clearing_price,None,False,False,'CAPITAL_MARKET_SHORTAGE')
    rate=float(market.clearing_price)
    audit=audit_priority_reset(
        existing_liability_claims,scenarios,new_money_principal=residual,
        promised_new_money_repayment=residual*(1.0+rate),lender_hurdle_rate=rate,
    )
    protected=bool(audit.protected_unlocking_positions)
    status='CAPITAL_CLEARS_AND_PROTECTED_PRIORITY_POSITION_EXISTS' if protected else 'CAPITAL_CLEARS_BUT_NO_PROTECTED_PRIORITY_POSITION'
    return CapitalPriorityPlan(funding_need,deployable,residual,market,rate,audit,True,protected,status)
