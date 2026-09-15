"""Marginal Clearing Price and Rent calculator (MCPR) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class Offer:
    name: str
    quantity: float
    price: float


@dataclass(frozen=True)
class Dispatch:
    name: str
    offered_quantity: float
    offer_price: float
    dispatched_quantity: float
    utilization: float
    revenue: float
    offered_variable_cost: float
    inframarginal_rent: float
    marginal_price_block: bool


@dataclass(frozen=True)
class MarketClear:
    demand: float
    served_quantity: float
    unserved_quantity: float
    clearing_price: float | None
    status: str
    total_uniform_payment: float
    total_as_bid_cost: float
    total_inframarginal_rent: float
    marginal_offer_names: tuple[str, ...]
    dispatch: tuple[Dispatch, ...]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["dispatch"] = [asdict(item) for item in self.dispatch]
        return payload


def clear_uniform_price_market(
    offers: Sequence[Offer],
    demand: float,
    *,
    scarcity_price: float | None = None,
    tolerance: float = 1e-12,
) -> MarketClear:
    """Clear divisible offers under merit order and a common marginal price."""

    records = tuple(offers)
    if len({offer.name for offer in records}) != len(records) or any(not offer.name for offer in records):
        raise ValueError("offer names must be non-empty and unique")
    if any(
        not np.isfinite(offer.quantity) or not np.isfinite(offer.price) or offer.quantity < 0
        for offer in records
    ):
        raise ValueError("offer quantities must be non-negative and offer prices finite")
    if not np.isfinite(demand) or demand < 0:
        raise ValueError("demand must be finite and non-negative")
    if scarcity_price is not None and not np.isfinite(scarcity_price):
        raise ValueError("scarcity price must be finite")
    if demand == 0:
        empty = tuple(
            Dispatch(o.name, o.quantity, o.price, 0.0, 0.0, 0.0, 0.0, 0.0, False)
            for o in records
        )
        return MarketClear(0.0, 0.0, 0.0, None, "NO_DEMAND", 0.0, 0.0, 0.0, (), empty)
    if not records or sum(o.quantity for o in records) <= tolerance:
        return MarketClear(demand, 0.0, demand, scarcity_price, "NO_CAPACITY", 0.0, 0.0, 0.0, (), ())

    ordered = sorted(records, key=lambda offer: (offer.price, offer.name))
    total_capacity = sum(offer.quantity for offer in ordered)
    shortage = demand > total_capacity + tolerance
    served = min(demand, total_capacity)
    if shortage:
        marginal_price = scarcity_price if scarcity_price is not None else max(o.price for o in ordered)
    else:
        cumulative = 0.0
        marginal_price = ordered[-1].price
        for offer in ordered:
            cumulative += offer.quantity
            if cumulative + tolerance >= demand:
                marginal_price = offer.price
                break

    below = [offer for offer in ordered if offer.price < marginal_price - tolerance]
    tied = [offer for offer in ordered if abs(offer.price - marginal_price) <= tolerance]
    accepted: dict[str, float] = {offer.name: 0.0 for offer in ordered}
    for offer in below:
        accepted[offer.name] = offer.quantity
    remaining = max(0.0, served - sum(offer.quantity for offer in below))
    tied_capacity = sum(offer.quantity for offer in tied)
    if tied_capacity > 0:
        fraction = min(1.0, remaining / tied_capacity)
        for offer in tied:
            accepted[offer.name] = offer.quantity * fraction
    if shortage:
        for offer in ordered:
            accepted[offer.name] = offer.quantity

    rows: list[Dispatch] = []
    for offer in records:
        quantity = accepted[offer.name]
        revenue = marginal_price * quantity
        offered_cost = offer.price * quantity
        rows.append(
            Dispatch(
                offer.name, offer.quantity, offer.price, quantity,
                quantity / offer.quantity if offer.quantity else 0.0,
                revenue, offered_cost, revenue - offered_cost,
                abs(offer.price - marginal_price) <= tolerance,
            )
        )
    return MarketClear(
        demand=float(demand),
        served_quantity=float(served),
        unserved_quantity=float(max(0.0, demand - served)),
        clearing_price=float(marginal_price),
        status="SHORTAGE" if shortage else "CLEARED",
        total_uniform_payment=float(sum(row.revenue for row in rows)),
        total_as_bid_cost=float(sum(row.offered_variable_cost for row in rows)),
        total_inframarginal_rent=float(sum(row.inframarginal_rent for row in rows)),
        marginal_offer_names=tuple(offer.name for offer in tied),
        dispatch=tuple(rows),
    )
