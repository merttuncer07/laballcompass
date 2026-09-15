"""Verified-Claim Priority Relief Ladder (VPRL) v0.1.

LCM monetizable asset-side claims are applied to a declared funding need first.
PRIU then audits only the residual new-money need. A counterfactual PRIU audit
shows how much priority pressure existed before verified liquidity conversion.
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
    from .parents.priu import Claim as LiabilityClaim, Scenario, PriorityResetAudit, audit_priority_reset
else:
    from parents.priu import Claim as LiabilityClaim, Scenario, PriorityResetAudit, audit_priority_reset

@dataclass(frozen=True)
class PriorityReliefResult:
    funding_need: float
    deployable_verified_liquidity: float
    residual_new_money_need: float
    liquidity_coverage_fraction: float
    counterfactual_priority_audit: PriorityResetAudit | None
    residual_priority_audit: PriorityResetAudit | None
    protected_positions_before: tuple[int, ...]
    protected_positions_after: tuple[int, ...]
    priority_protection_improved: bool
    status: str
    def to_dict(self): return asdict(self)


def plan_priority_relief(
    *, funding_need: float, liquidity_claims: Sequence[LiquidityClaim], funding_channels: Sequence[FundingChannel],
    existing_liability_claims: Sequence[LiabilityClaim], scenarios: Sequence[Scenario],
    horizon_days: int = 0, promised_repayment_markup: float = 0.10, lender_hurdle_rate: float = 0.0,
) -> PriorityReliefResult:
    if not math.isfinite(funding_need) or funding_need < 0:
        raise ValueError("funding_need must be finite and non-negative")
    if promised_repayment_markup < 0 or lender_hurdle_rate < 0:
        raise ValueError("markup and hurdle rate must be non-negative")
    lcm=LiquidityConversionMap(liquidity_claims,funding_channels).solve(horizon_days=horizon_days)
    deployable=float(lcm['deployable_liquidity'])
    applied=min(funding_need,deployable)
    residual=max(0.0,funding_need-applied)
    coverage=1.0 if funding_need==0 else applied/funding_need

    def priu(amount: float):
        if amount <= 1e-12: return None
        return audit_priority_reset(
            existing_liability_claims,scenarios,new_money_principal=amount,
            promised_new_money_repayment=amount*(1.0+promised_repayment_markup),lender_hurdle_rate=lender_hurdle_rate,
        )
    counter=priu(funding_need)
    after=priu(residual)
    before_positions=counter.protected_unlocking_positions if counter else ()
    after_positions=after.protected_unlocking_positions if after else ()
    improved=(residual < funding_need-1e-12) and (bool(after_positions) and not bool(before_positions) or residual <= 1e-12)
    if residual <= 1e-12:
        status='VERIFIED_LIQUIDITY_FULLY_COVERS_NEED_NO_PRIORITY_RESET_REQUIRED'
    elif improved:
        status='VERIFIED_LIQUIDITY_REDUCES_NEW_MONEY_AND_IMPROVES_PRIORITY_PROTECTION'
    elif residual < funding_need-1e-12:
        status='VERIFIED_LIQUIDITY_REDUCES_NEW_MONEY_NEED'
    else:
        status='NO_VERIFIED_LIQUIDITY_RELIEF'
    return PriorityReliefResult(
        funding_need,deployable,residual,coverage,counter,after,before_positions,after_positions,improved,status
    )
