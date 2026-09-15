"""Ownership Wedge Network Mapper (OWNM)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


@dataclass(frozen=True)
class OwnershipControlResult:
    company_names: tuple[str, ...]
    ultimate_cash_exposure: np.ndarray
    commanded_voting_power: np.ndarray
    controlled: np.ndarray
    control_round: np.ndarray
    control_to_cash_wedge: np.ndarray
    controlled_asset_value: float
    cash_at_risk_value: float
    controlled_asset_to_cash_at_risk: float
    cross_ownership_components: tuple[tuple[str, ...], ...]


class OwnershipWedgeNetworkMapper:
    """Separate linear cash-flow exposure from thresholded voting control propagation."""

    def __init__(
        self,
        company_names: list[str],
        company_cash_holdings: np.ndarray,
        company_vote_holdings: np.ndarray,
        control_thresholds: np.ndarray | float = 0.5,
    ) -> None:
        self.names = tuple(company_names)
        self.cash = np.asarray(company_cash_holdings, dtype=float)
        self.votes = np.asarray(company_vote_holdings, dtype=float)
        n = len(self.names)
        if self.cash.shape != (n, n) or self.votes.shape != (n, n):
            raise ValueError("holding matrices must be square and match company names")
        if np.any(self.cash < 0) or np.any(self.votes < 0):
            raise ValueError("holdings cannot be negative")
        self.thresholds = np.broadcast_to(np.asarray(control_thresholds, dtype=float), (n,)).copy()
        spectral_radius = max(abs(np.linalg.eigvals(self.cash)), default=0.0)
        if spectral_radius >= 1.0 - 1e-12:
            raise ValueError("cash-flow cross-holdings do not admit a finite exposure inverse")

    def _cross_ownership_components(self) -> tuple[tuple[str, ...], ...]:
        adjacency = ((self.cash + self.votes) > 0).astype(int)
        component_count, labels = connected_components(
            csr_matrix(adjacency), directed=True, connection="strong"
        )
        components = []
        for label in range(component_count):
            members = np.flatnonzero(labels == label)
            if members.size > 1 or (members.size == 1 and adjacency[members[0], members[0]]):
                components.append(tuple(self.names[index] for index in members))
        return tuple(components)

    def analyze(
        self,
        investor_direct_cash: np.ndarray,
        investor_direct_votes: np.ndarray,
        company_asset_values: np.ndarray | None = None,
    ) -> OwnershipControlResult:
        n = len(self.names)
        direct_cash = np.asarray(investor_direct_cash, dtype=float)
        direct_votes = np.asarray(investor_direct_votes, dtype=float)
        if direct_cash.shape != (n,) or direct_votes.shape != (n,):
            raise ValueError("investor vectors have wrong dimension")
        ultimate_cash = direct_cash @ np.linalg.inv(np.eye(n) - self.cash)
        controlled = np.zeros(n, dtype=bool)
        control_round = np.full(n, -1, dtype=int)
        commanded = direct_votes.copy()
        round_number = 0
        while True:
            newly_controlled = (~controlled) & (commanded >= self.thresholds - 1e-12)
            if not np.any(newly_controlled):
                break
            controlled[newly_controlled] = True
            control_round[newly_controlled] = round_number
            commanded = direct_votes + self.votes[controlled].sum(axis=0)
            round_number += 1
            if round_number > n:
                break
        wedge = np.zeros(n)
        positive = ultimate_cash > 1e-12
        wedge[controlled & positive] = 1.0 / ultimate_cash[controlled & positive]
        wedge[controlled & ~positive] = np.inf
        assets = np.ones(n) if company_asset_values is None else np.asarray(company_asset_values, dtype=float)
        controlled_value = float(assets[controlled].sum())
        cash_at_risk = float(ultimate_cash @ assets)
        leverage = controlled_value / cash_at_risk if cash_at_risk > 0 else float("inf")
        return OwnershipControlResult(
            company_names=self.names,
            ultimate_cash_exposure=ultimate_cash,
            commanded_voting_power=commanded,
            controlled=controlled,
            control_round=control_round,
            control_to_cash_wedge=wedge,
            controlled_asset_value=controlled_value,
            cash_at_risk_value=cash_at_risk,
            controlled_asset_to_cash_at_risk=leverage,
            cross_ownership_components=self._cross_ownership_components(),
        )

