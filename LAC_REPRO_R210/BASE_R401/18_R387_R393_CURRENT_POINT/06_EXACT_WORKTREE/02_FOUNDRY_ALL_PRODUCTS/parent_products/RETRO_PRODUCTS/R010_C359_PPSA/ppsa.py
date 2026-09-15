"""Privacy Pipeline Safety Accountant (PPSA) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Sequence

import numpy as np


@dataclass(frozen=True)
class Release:
    release_id: str
    kind: Literal["MECHANISM", "POST_PROCESS"]
    epsilon: float = 0.0
    delta: float = 0.0
    parent_release_id: str | None = None
    accesses_raw_data: bool = False


@dataclass(frozen=True)
class PrivacyAccount:
    mechanism_count: int
    post_processing_count: int
    basic_epsilon: float
    basic_delta: float
    advanced_epsilon: float | None
    advanced_delta: float | None
    reported_epsilon: float
    reported_delta: float
    accounting_method: str
    epsilon_budget: float
    delta_budget: float
    epsilon_utilization: float
    delta_utilization: float
    within_budget: bool
    charged_release_ids: tuple[str, ...]
    zero_cost_post_processing_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def account_privacy(
    releases: Sequence[Release],
    *,
    epsilon_budget: float,
    delta_budget: float,
    advanced_delta_slack: float | None = None,
) -> PrivacyAccount:
    """Account sequential composition and data-independent post-processing."""

    if (
        not np.isfinite(epsilon_budget)
        or not np.isfinite(delta_budget)
        or epsilon_budget < 0
        or not 0 <= delta_budget < 1
    ):
        raise ValueError("budgets must be finite with epsilon>=0 and delta in [0,1)")
    if advanced_delta_slack is not None and (
        not np.isfinite(advanced_delta_slack) or not 0 < advanced_delta_slack < 1
    ):
        raise ValueError("advanced_delta_slack must lie strictly between zero and one")

    seen: set[str] = set()
    mechanisms: list[Release] = []
    post_ids: list[str] = []
    for release in releases:
        if not release.release_id or release.release_id in seen:
            raise ValueError("release IDs must be non-empty and unique")
        if release.kind == "MECHANISM":
            if (
                release.parent_release_id is not None
                or not np.isfinite(release.epsilon)
                or not np.isfinite(release.delta)
                or release.epsilon < 0
                or not 0 <= release.delta < 1
            ):
                raise ValueError("mechanisms require finite non-negative epsilon/delta and no parent")
            mechanisms.append(release)
        elif release.kind == "POST_PROCESS":
            if release.parent_release_id not in seen:
                raise ValueError("post-processing parent must be an earlier release")
            if release.accesses_raw_data:
                raise ValueError("a step that accesses raw data is not post-processing; declare a mechanism")
            if release.epsilon != 0 or release.delta != 0:
                raise ValueError("post-processing steps must not declare a new privacy charge")
            post_ids.append(release.release_id)
        else:
            raise ValueError(f"unknown release kind: {release.kind}")
        seen.add(release.release_id)

    epsilons = np.asarray([release.epsilon for release in mechanisms], dtype=float)
    deltas = np.asarray([release.delta for release in mechanisms], dtype=float)
    basic_epsilon = float(np.sum(epsilons))
    basic_delta = float(np.sum(deltas))
    advanced_epsilon = advanced_delta = None
    method = "BASIC_SEQUENTIAL_COMPOSITION"
    reported_epsilon, reported_delta = basic_epsilon, basic_delta
    if advanced_delta_slack is not None and len(mechanisms):
        advanced_epsilon = float(
            np.sqrt(2.0 * np.log(1.0 / advanced_delta_slack) * np.sum(epsilons**2))
            + np.sum(epsilons * np.expm1(epsilons))
        )
        advanced_delta = float(basic_delta + advanced_delta_slack)
        if advanced_epsilon < basic_epsilon:
            method = "ADVANCED_SEQUENTIAL_COMPOSITION"
            reported_epsilon, reported_delta = advanced_epsilon, advanced_delta

    within = reported_epsilon <= epsilon_budget + 1e-12 and reported_delta <= delta_budget + 1e-15
    epsilon_utilization = float(reported_epsilon / epsilon_budget) if epsilon_budget else (
        0.0 if reported_epsilon == 0 else float("inf")
    )
    delta_utilization = float(reported_delta / delta_budget) if delta_budget else (
        0.0 if reported_delta == 0 else float("inf")
    )
    return PrivacyAccount(
        mechanism_count=len(mechanisms),
        post_processing_count=len(post_ids),
        basic_epsilon=basic_epsilon,
        basic_delta=basic_delta,
        advanced_epsilon=advanced_epsilon,
        advanced_delta=advanced_delta,
        reported_epsilon=reported_epsilon,
        reported_delta=reported_delta,
        accounting_method=method,
        epsilon_budget=float(epsilon_budget),
        delta_budget=float(delta_budget),
        epsilon_utilization=epsilon_utilization,
        delta_utilization=delta_utilization,
        within_budget=within,
        charged_release_ids=tuple(release.release_id for release in mechanisms),
        zero_cost_post_processing_ids=tuple(post_ids),
    )
