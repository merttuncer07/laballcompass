"""Priority-Reset Investment Unlocker (PRIU) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class Claim:
    name: str
    amount: float


@dataclass(frozen=True)
class Scenario:
    probability: float
    asset_value_without_funding: float
    asset_value_if_funded: float


@dataclass(frozen=True)
class PriorityArrangement:
    new_money_position: int
    priority_order: tuple[str, ...]
    expected_new_money_recovery: float
    lender_required_recovery: float
    lender_npv: float
    financing_unlocked: bool
    baseline_existing_recoveries: dict[str, float]
    funded_existing_recoveries: dict[str, float]
    existing_recovery_changes: dict[str, float]
    all_existing_claims_protected: bool
    enterprise_incremental_value_net_of_funding: float
    expected_unallocated_residual: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PriorityResetAudit:
    arrangements: tuple[PriorityArrangement, ...]
    least_disruptive_unlocking_position: int | None
    protected_unlocking_positions: tuple[int, ...]

    def to_dict(self) -> dict:
        return {
            "arrangements": [item.to_dict() for item in self.arrangements],
            "least_disruptive_unlocking_position": self.least_disruptive_unlocking_position,
            "protected_unlocking_positions": list(self.protected_unlocking_positions),
        }


def _waterfall(asset_value: float, claims: Sequence[Claim]) -> tuple[dict[str, float], float]:
    remaining = float(asset_value)
    recoveries: dict[str, float] = {}
    for claim in claims:
        payment = min(claim.amount, remaining)
        recoveries[claim.name] = payment
        remaining -= payment
    return recoveries, remaining


def audit_priority_reset(
    existing_claims: Sequence[Claim],
    scenarios: Sequence[Scenario],
    *,
    new_money_principal: float,
    promised_new_money_repayment: float,
    lender_hurdle_rate: float = 0.0,
    protection_tolerance: float = 1e-10,
) -> PriorityResetAudit:
    """Compare every insertion position for new money in an absolute-priority waterfall."""

    claims = tuple(existing_claims)
    states = tuple(scenarios)
    if not claims or len({claim.name for claim in claims}) != len(claims):
        raise ValueError("existing claims must have unique names and cannot be empty")
    if any(not claim.name or not np.isfinite(claim.amount) or claim.amount < 0 for claim in claims):
        raise ValueError("claim names must be non-empty and amounts finite/non-negative")
    if not states or any(
        not np.isfinite(state.probability)
        or not np.isfinite(state.asset_value_without_funding)
        or not np.isfinite(state.asset_value_if_funded)
        or state.probability < 0
        or state.asset_value_without_funding < 0
        or state.asset_value_if_funded < 0
        for state in states
    ):
        raise ValueError("scenarios must contain finite non-negative probabilities and asset values")
    probability_sum = sum(state.probability for state in states)
    if not np.isclose(probability_sum, 1.0, atol=1e-10):
        raise ValueError("scenario probabilities must sum to one")
    if (
        not np.isfinite(new_money_principal)
        or not np.isfinite(promised_new_money_repayment)
        or new_money_principal < 0
        or promised_new_money_repayment < 0
        or lender_hurdle_rate < 0
    ):
        raise ValueError("new-money terms and hurdle rate must be finite and non-negative")

    baseline = {claim.name: 0.0 for claim in claims}
    expected_without = expected_funded = 0.0
    for state in states:
        recovery, _ = _waterfall(state.asset_value_without_funding, claims)
        for name, value in recovery.items():
            baseline[name] += state.probability * value
        expected_without += state.probability * state.asset_value_without_funding
        expected_funded += state.probability * state.asset_value_if_funded

    required = new_money_principal * (1.0 + lender_hurdle_rate)
    arrangements: list[PriorityArrangement] = []
    for position in range(len(claims) + 1):
        new_claim = Claim("NEW_MONEY", promised_new_money_repayment)
        ordered = claims[:position] + (new_claim,) + claims[position:]
        funded_existing = {claim.name: 0.0 for claim in claims}
        new_recovery = residual = 0.0
        for state in states:
            recovery, state_residual = _waterfall(state.asset_value_if_funded, ordered)
            new_recovery += state.probability * recovery["NEW_MONEY"]
            residual += state.probability * state_residual
            for claim in claims:
                funded_existing[claim.name] += state.probability * recovery[claim.name]
        changes = {name: funded_existing[name] - baseline[name] for name in baseline}
        arrangements.append(
            PriorityArrangement(
                new_money_position=position,
                priority_order=tuple(claim.name for claim in ordered),
                expected_new_money_recovery=new_recovery,
                lender_required_recovery=required,
                lender_npv=new_recovery - required,
                financing_unlocked=new_recovery + protection_tolerance >= required,
                baseline_existing_recoveries=dict(baseline),
                funded_existing_recoveries=funded_existing,
                existing_recovery_changes=changes,
                all_existing_claims_protected=all(value >= -protection_tolerance for value in changes.values()),
                enterprise_incremental_value_net_of_funding=expected_funded - expected_without - new_money_principal,
                expected_unallocated_residual=residual,
            )
        )

    unlocking = [item for item in arrangements if item.financing_unlocked]
    protected = tuple(item.new_money_position for item in unlocking if item.all_existing_claims_protected)
    # A larger insertion index is less senior and therefore changes the old order less.
    least_disruptive = max((item.new_money_position for item in unlocking), default=None)
    return PriorityResetAudit(tuple(arrangements), least_disruptive, protected)
