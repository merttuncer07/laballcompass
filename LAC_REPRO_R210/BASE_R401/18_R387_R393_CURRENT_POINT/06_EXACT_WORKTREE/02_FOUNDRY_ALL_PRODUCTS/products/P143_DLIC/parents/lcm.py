"""Liquidity Conversion Map, built from IM-452 -> IM-015."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Sequence

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class Claim:
    claim_id: str
    face_value: float
    anchor: str
    claim_type: str
    verifier: str
    verified: bool
    verification_latency_days: int = 0


@dataclass(frozen=True)
class FundingChannel:
    name: str
    liquidity_capacity: float
    accepted_verifiers: tuple[str, ...]
    accepted_claim_types: tuple[str, ...]
    advance_rate: float
    max_anchor_fraction: float = 1.0


@dataclass(frozen=True)
class FundingAllocation:
    claim_id: str
    channel: str
    financed_face: float
    deployable_liquidity: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class LiquidityConversionMap:
    def __init__(self, claims: Sequence[Claim], channels: Sequence[FundingChannel]) -> None:
        self.claims = tuple(claims)
        self.channels = tuple(channels)
        if any(claim.face_value < 0 for claim in claims):
            raise ValueError("Claim face values must be non-negative")
        for channel in channels:
            if channel.liquidity_capacity < 0:
                raise ValueError("Channel capacity must be non-negative")
            if not 0 < channel.advance_rate <= 1:
                raise ValueError("advance_rate must be in (0, 1]")
            if not 0 < channel.max_anchor_fraction <= 1:
                raise ValueError("max_anchor_fraction must be in (0, 1]")

    @staticmethod
    def _eligible(claim: Claim, channel: FundingChannel, horizon_days: int) -> bool:
        return (
            claim.verified
            and claim.verification_latency_days <= horizon_days
            and claim.verifier in channel.accepted_verifiers
            and claim.claim_type in channel.accepted_claim_types
        )

    def solve(self, horizon_days: int = 0) -> dict[str, Any]:
        if horizon_days < 0:
            raise ValueError("horizon_days must be non-negative")
        pairs = [
            (claim_index, channel_index)
            for claim_index, claim in enumerate(self.claims)
            for channel_index, channel in enumerate(self.channels)
            if self._eligible(claim, channel, horizon_days)
        ]
        nominal = sum(claim.face_value for claim in self.claims)
        verified = sum(
            claim.face_value
            for claim in self.claims
            if claim.verified and claim.verification_latency_days <= horizon_days
        )
        financeable_ids = {self.claims[i].claim_id for i, _ in pairs}
        financeable_face = sum(
            claim.face_value for claim in self.claims if claim.claim_id in financeable_ids
        )
        if not pairs:
            return {
                "nominal_resource": nominal,
                "verified_resource": verified,
                "financeable_face": 0.0,
                "deployable_liquidity": 0.0,
                "allocations": [],
                "unused_nominal": nominal,
            }

        objective = np.array([-self.channels[j].advance_rate for i, j in pairs])
        rows: list[list[float]] = []
        bounds: list[float] = []

        for claim_index, claim in enumerate(self.claims):
            rows.append([1.0 if i == claim_index else 0.0 for i, j in pairs])
            bounds.append(claim.face_value)
        for channel_index, channel in enumerate(self.channels):
            rows.append(
                [channel.advance_rate if j == channel_index else 0.0 for i, j in pairs]
            )
            bounds.append(channel.liquidity_capacity)
        for channel_index, channel in enumerate(self.channels):
            anchors = sorted({claim.anchor for claim in self.claims})
            for anchor in anchors:
                rows.append(
                    [
                        channel.advance_rate
                        if j == channel_index and self.claims[i].anchor == anchor
                        else 0.0
                        for i, j in pairs
                    ]
                )
                bounds.append(channel.liquidity_capacity * channel.max_anchor_fraction)

        result = linprog(
            objective,
            A_ub=np.asarray(rows),
            b_ub=np.asarray(bounds),
            bounds=[(0.0, None)] * len(pairs),
            method="highs",
        )
        if not result.success:
            raise RuntimeError(f"Liquidity allocation failed: {result.message}")

        allocations = []
        for amount, (i, j) in zip(result.x, pairs):
            if amount > 1e-8:
                channel = self.channels[j]
                allocations.append(
                    FundingAllocation(
                        self.claims[i].claim_id,
                        channel.name,
                        float(amount),
                        float(amount * channel.advance_rate),
                    )
                )
        deployable = sum(item.deployable_liquidity for item in allocations)
        return {
            "nominal_resource": nominal,
            "verified_resource": verified,
            "financeable_face": financeable_face,
            "deployable_liquidity": deployable,
            "allocations": [item.as_dict() for item in allocations],
            "unused_nominal": nominal - sum(item.financed_face for item in allocations),
        }

    def marginal_verification_value(
        self, claim_id: str, verifier: str, horizon_days: int = 0
    ) -> dict[str, float]:
        before = self.solve(horizon_days)
        updated = [
            replace(claim, verified=True, verifier=verifier, verification_latency_days=0)
            if claim.claim_id == claim_id
            else claim
            for claim in self.claims
        ]
        if all(claim.claim_id != claim_id for claim in self.claims):
            raise KeyError(f"Unknown claim: {claim_id}")
        after = LiquidityConversionMap(updated, self.channels).solve(horizon_days)
        return {
            "before_deployable": before["deployable_liquidity"],
            "after_deployable": after["deployable_liquidity"],
            "marginal_deployable_liquidity": after["deployable_liquidity"]
            - before["deployable_liquidity"],
        }
