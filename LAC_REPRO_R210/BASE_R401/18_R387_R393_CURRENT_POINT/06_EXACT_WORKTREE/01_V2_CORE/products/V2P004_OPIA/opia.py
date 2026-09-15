from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np
from numpy.polynomial.hermite import hermgauss

# Reuse the exact packaged P138 consumer implementation and its channel type.
# K081's neutral confounding/backaction mechanism is reimplemented locally;
# the monolithic LCB prototype library is intentionally not imported.
_REPO = Path(__file__).resolve().parents[3]
_FOUNDRY_PRODUCTS = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products"
if str(_FOUNDRY_PRODUCTS) not in sys.path:
    sys.path.insert(0, str(_FOUNDRY_PRODUCTS))

from P138_SPIA.spia import acquire_for_search_policy  # noqa: E402
from P138_SPIA.parents.aicc import InformationChannel  # noqa: E402


@dataclass(frozen=True)
class ObservationPolicyHistory:
    channel_name: str
    passive_proxy: Sequence[float]
    observed: Sequence[int]
    next_contrast_state: Sequence[float]
    proxy_grid: Sequence[float]
    posterior_mean_if_unobserved: Sequence[float]
    posterior_mean_if_observed: Sequence[float]
    effect_contrast: Sequence[float]


@dataclass(frozen=True)
class BackactionEstimate:
    channel_name: str
    adjusted_coefficient: float
    naive_observed_minus_unobserved: float
    state_coefficient: float
    belief_shift: tuple[float, ...]
    status: str


@dataclass(frozen=True)
class GuardedChannelValue:
    name: str
    base_expected_decision_improvement: float
    adjusted_expected_utility_change: float
    cost: float
    base_net_value: float
    adjusted_net_value: float
    backaction_coefficient: float


@dataclass(frozen=True)
class OPIAResult:
    policy_names: tuple[str, ...]
    detection_time_vectors: tuple[tuple[float, ...], ...]
    current_policy: str
    base_chosen_channel: str | None
    chosen_channel: str | None
    base_ranked_channels: tuple[dict, ...]
    ranked_channels: tuple[dict, ...]
    backaction_estimates: tuple[dict, ...]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _posterior_state_from_policy(history: ObservationPolicyHistory) -> np.ndarray:
    proxy = np.asarray(history.passive_proxy, dtype=float)
    observed = np.asarray(history.observed, dtype=int)
    grid = np.asarray(history.proxy_grid, dtype=float)
    p0 = np.asarray(history.posterior_mean_if_unobserved, dtype=float)
    p1 = np.asarray(history.posterior_mean_if_observed, dtype=float)
    if proxy.ndim != 1 or observed.shape != proxy.shape:
        raise ValueError("passive_proxy and observed must be aligned vectors")
    if grid.ndim != 1 or p0.shape != grid.shape or p1.shape != grid.shape or grid.size < 2:
        raise ValueError("proxy-grid posterior curves must align")
    if np.any(np.diff(grid) <= 0):
        raise ValueError("proxy_grid must be strictly increasing")
    if not np.all(np.isin(observed, [0, 1])):
        raise ValueError("observed must be binary")
    out = np.empty_like(proxy)
    mask = observed.astype(bool)
    out[~mask] = np.interp(proxy[~mask], grid, p0)
    out[mask] = np.interp(proxy[mask], grid, p1)
    return out


def _estimate_backaction(history: ObservationPolicyHistory, state_dim: int) -> BackactionEstimate:
    observed = np.asarray(history.observed, dtype=float)
    y = np.asarray(history.next_contrast_state, dtype=float)
    posterior = _posterior_state_from_policy(history)
    if y.shape != posterior.shape or y.size < 6 or not np.all(np.isfinite(y)):
        raise ValueError("next_contrast_state must be a finite aligned history with at least six rows")
    if observed.sum() == 0 or observed.sum() == len(observed):
        raise ValueError("history must contain observed and unobserved rows")
    X = np.column_stack([np.ones(len(y)), observed, posterior])
    if np.linalg.matrix_rank(X) < 3:
        raise ValueError("observation-policy history does not identify a separate backaction coefficient")
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    adjusted = float(coef[1])
    state_coef = float(coef[2])
    naive = float(y[observed == 1].mean() - y[observed == 0].mean())

    contrast = np.asarray(history.effect_contrast, dtype=float)
    if contrast.shape != (state_dim,) or not np.all(np.isfinite(contrast)):
        raise ValueError("effect_contrast must match the P138 belief dimension")
    if abs(float(contrast.sum())) > 1e-10:
        raise ValueError("effect_contrast must lie in the probability-simplex tangent space")
    norm2 = float(contrast @ contrast)
    if norm2 <= 0:
        raise ValueError("effect_contrast must be nonzero")
    shift = adjusted * contrast / norm2
    return BackactionEstimate(
        channel_name=history.channel_name,
        adjusted_coefficient=adjusted,
        naive_observed_minus_unobserved=naive,
        state_coefficient=state_coef,
        belief_shift=tuple(map(float, shift)),
        status="OBSERVATION_POLICY_ADJUSTED_BACKACTION_ESTIMATED",
    )


def _adjusted_channel_value(
    mean: np.ndarray,
    covariance: np.ndarray,
    slopes: np.ndarray,
    channel: InformationChannel,
    estimate: BackactionEstimate,
    *,
    quadrature_points: int = 31,
) -> GuardedChannelValue:
    h = np.asarray(channel.measurement_vector, dtype=float)
    shift = np.asarray(estimate.belief_shift, dtype=float)
    shifted_mean = mean + shift
    if abs(float(shift.sum())) > 1e-10:
        raise ValueError("estimated backaction shift left the simplex tangent space")
    if np.any(shifted_mean < -1e-10) or np.any(shifted_mean > 1 + 1e-10) or not np.isclose(shifted_mean.sum(), 1.0):
        raise ValueError("estimated backaction would move the expected belief outside the probability simplex")

    predictive_variance = float(h @ covariance @ h + channel.noise_variance)
    if predictive_variance <= 0:
        adjusted_change = float("-inf")
    else:
        gain = covariance @ h / predictive_variance
        nodes, weights = hermgauss(int(quadrature_points))
        weights = weights / np.sqrt(np.pi)
        current_value = float(np.max(slopes @ mean))
        posterior_value = 0.0
        for node, weight in zip(nodes, weights):
            residual = np.sqrt(2.0 * predictive_variance) * node
            posterior_mean = mean + gain * residual + shift
            posterior_value += float(weight) * float(np.max(slopes @ posterior_mean))
        # Unlike ordinary information value, a physical observation can hurt.
        # Therefore do not clamp this change at zero.
        adjusted_change = float(posterior_value - current_value)

    return GuardedChannelValue(
        name=channel.name,
        base_expected_decision_improvement=float("nan"),
        adjusted_expected_utility_change=adjusted_change,
        cost=float(channel.cost),
        base_net_value=float("nan"),
        adjusted_net_value=float(adjusted_change - float(channel.cost)),
        backaction_coefficient=float(estimate.adjusted_coefficient),
    )


def acquire_for_search_policy_with_backaction_guard(
    belief_mean,
    belief_covariance,
    *,
    policies,
    channels,
    observation_histories: Mapping[str, ObservationPolicyHistory],
    policy_kwargs=None,
) -> OPIAResult:
    """P138 search-policy acquisition with K081-style confounding-safe backaction.

    P138 retains authority over the search-policy utility geometry.  For each
    candidate measurement channel, the adapter requires historical observation
    metadata plus a passive state proxy.  It estimates the observation-induced
    change on a declared scalar contrast after controlling reconstructed state,
    maps that scalar effect to the minimum-norm simplex-tangent belief shift, and
    includes that shift in the acquisition value calculation.

    Missing channel-specific backaction history fails closed.
    """
    mean = np.asarray(belief_mean, dtype=float)
    covariance = np.asarray(belief_covariance, dtype=float)

    # First execute the exact P138 path.  This preserves all of P138's probability
    # simplex/channel/policy validation and yields the canonical policy utilities.
    base = acquire_for_search_policy(
        mean,
        covariance,
        policies=policies,
        channels=channels,
        policy_kwargs=policy_kwargs,
    )

    channel_names = [str(ch.name) for ch in channels]
    missing = [name for name in channel_names if name not in observation_histories]
    extra = [name for name in observation_histories if name not in channel_names]
    if missing:
        raise ValueError(f"backaction history required for every candidate channel; missing={missing}")
    if extra:
        raise ValueError(f"backaction history supplied for unknown channels: {extra}")

    slopes = -np.asarray(base.detection_time_vectors, dtype=float)
    base_by_name = {str(row["name"]): dict(row) for row in base.ranked_channels}
    estimates = []
    guarded = []
    for channel in channels:
        estimate = _estimate_backaction(observation_histories[channel.name], mean.size)
        if estimate.channel_name != channel.name:
            raise ValueError("history channel_name does not match the channel key")
        row = _adjusted_channel_value(mean, covariance, slopes, channel, estimate)
        b = base_by_name[channel.name]
        guarded.append(GuardedChannelValue(
            name=row.name,
            base_expected_decision_improvement=float(b["expected_decision_improvement"]),
            adjusted_expected_utility_change=row.adjusted_expected_utility_change,
            cost=row.cost,
            base_net_value=float(b["net_value"]),
            adjusted_net_value=row.adjusted_net_value,
            backaction_coefficient=row.backaction_coefficient,
        ))
        estimates.append(estimate)

    guarded.sort(key=lambda x: x.adjusted_net_value, reverse=True)
    chosen = guarded[0].name if guarded and guarded[0].adjusted_net_value > 0 else None
    return OPIAResult(
        policy_names=base.policy_names,
        detection_time_vectors=base.detection_time_vectors,
        current_policy=base.current_policy,
        base_chosen_channel=base.chosen_channel,
        chosen_channel=chosen,
        base_ranked_channels=base.ranked_channels,
        ranked_channels=tuple(asdict(x) for x in guarded),
        backaction_estimates=tuple(asdict(x) for x in estimates),
        status="OBSERVATION_POLICY_BACKACTION_GUARDED_SEARCH_ACQUISITION_COMPLETE",
    )
