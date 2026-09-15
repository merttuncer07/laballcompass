"""Decision-private composition governor (DPCG) v0.1."""
from __future__ import annotations

from typing import Mapping

if __package__:
    from .parents.dtpr import DecisionSpec, DecisionTargetedPrivateRelease, PrivateActionRelease
else:
    from parents.dtpr import DecisionSpec, DecisionTargetedPrivateRelease, PrivateActionRelease
if __package__:
    from .parents.ppsa import PrivacyAccount, Release, account_privacy
else:
    from parents.ppsa import PrivacyAccount, Release, account_privacy


class GlobalPrivateDecisionCoordinator:
    def __init__(self, *, epsilon_budget: float, delta_budget: float = 0.0) -> None:
        if epsilon_budget <= 0:
            raise ValueError("epsilon_budget must be positive")
        self.epsilon_budget = float(epsilon_budget)
        self.delta_budget = float(delta_budget)
        self._releases: list[Release] = []

    @property
    def releases(self) -> tuple[Release, ...]:
        return tuple(self._releases)

    def account(self) -> PrivacyAccount:
        return account_privacy(
            self._releases,
            epsilon_budget=self.epsilon_budget,
            delta_budget=self.delta_budget,
        )

    def _preflight(self, epsilon: float, delta: float = 0.0) -> None:
        candidate = self._releases + [
            Release("__preflight__", "MECHANISM", epsilon=epsilon, delta=delta)
        ]
        if not account_privacy(
            candidate,
            epsilon_budget=self.epsilon_budget,
            delta_budget=self.delta_budget,
        ).within_budget:
            raise RuntimeError("global privacy budget would be exceeded")

    def release_action(
        self,
        *,
        release_id: str,
        controller: DecisionTargetedPrivateRelease,
        spec: DecisionSpec,
        true_score: float,
        epsilon: float,
    ) -> PrivateActionRelease:
        if any(release.release_id == release_id for release in self._releases):
            raise ValueError("release_id must be globally unique")
        self._preflight(epsilon)
        # Global preflight runs before DTPR touches its local budget or private data.
        result = controller.release(spec, true_score, epsilon)
        self._releases.append(Release(release_id, "MECHANISM", epsilon=epsilon, delta=0.0))
        return result

    def add_post_process(self, *, release_id: str, parent_release_id: str) -> None:
        candidate = self._releases + [
            Release(
                release_id,
                "POST_PROCESS",
                parent_release_id=parent_release_id,
                accesses_raw_data=False,
            )
        ]
        # PPSA validates ordering, parent existence, zero charge, and raw-data isolation.
        account_privacy(
            candidate,
            epsilon_budget=self.epsilon_budget,
            delta_budget=self.delta_budget,
        )
        self._releases = candidate
