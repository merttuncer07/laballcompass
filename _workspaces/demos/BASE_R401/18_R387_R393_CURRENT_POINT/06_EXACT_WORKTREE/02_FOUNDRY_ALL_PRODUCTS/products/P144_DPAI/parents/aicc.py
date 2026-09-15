"""Adaptive Information-Channel Controller (AICC)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.hermite import hermgauss


@dataclass(frozen=True)
class InformationChannel:
    name: str
    measurement_vector: np.ndarray
    noise_variance: float
    cost: float = 0.0

    def __post_init__(self):
        h = np.asarray(self.measurement_vector, dtype=float)
        if h.ndim != 1 or not h.size or not np.all(np.isfinite(h)):
            raise ValueError("measurement_vector must be a finite state vector")
        if not self.name or not np.isfinite(self.noise_variance) or self.noise_variance < 0 or not np.isfinite(self.cost) or self.cost < 0:
            raise ValueError("channel name, non-negative finite noise and cost are required")


@dataclass(frozen=True)
class ChannelValue:
    name: str
    expected_decision_improvement: float
    cost: float
    net_value: float


class AdaptiveInformationController:
    """Select the available Gaussian channel with maximum downstream decision value."""

    def __init__(
        self,
        belief_mean: np.ndarray,
        belief_covariance: np.ndarray,
        action_slopes: np.ndarray,
        action_intercepts: np.ndarray,
        channels: list[InformationChannel],
        quadrature_points: int = 31,
    ) -> None:
        self.mean = np.asarray(belief_mean, dtype=float)
        self.covariance = np.asarray(belief_covariance, dtype=float)
        self.action_slopes = np.asarray(action_slopes, dtype=float)
        self.action_intercepts = np.asarray(action_intercepts, dtype=float)
        self.channels = list(channels)
        if self.mean.ndim != 1 or not self.mean.size or not np.all(np.isfinite(self.mean)):
            raise ValueError("belief mean must be a finite state vector")
        d = self.mean.size
        if self.covariance.shape != (d, d) or not np.all(np.isfinite(self.covariance)) or not np.allclose(self.covariance, self.covariance.T):
            raise ValueError("belief covariance must be finite and symmetric")
        if np.linalg.eigvalsh(self.covariance).min() < -1e-12:
            raise ValueError("belief covariance must be positive semidefinite")
        if self.action_slopes.ndim != 2 or not self.action_slopes.shape[0] or self.action_intercepts.shape != (self.action_slopes.shape[0],) or not np.all(np.isfinite(self.action_slopes)) or not np.all(np.isfinite(self.action_intercepts)):
            raise ValueError("finite action slopes and matching intercepts are required")
        if len({c.name for c in self.channels}) != len(self.channels):
            raise ValueError("channel names must be unique")
        if any(np.asarray(c.measurement_vector).shape != (d,) for c in self.channels):
            raise ValueError("channel and state dimensions differ")
        if not isinstance(quadrature_points, int) or quadrature_points < 2:
            raise ValueError("quadrature_points must be an integer at least two")
        self.nodes, self.weights = hermgauss(quadrature_points)
        self.weights = self.weights / np.sqrt(np.pi)
        if self.action_slopes.shape[1] != self.mean.size:
            raise ValueError("action and state dimensions differ")

    def expected_action_utilities(self, mean: np.ndarray | None = None) -> np.ndarray:
        location = self.mean if mean is None else np.asarray(mean, dtype=float)
        return self.action_slopes @ location + self.action_intercepts

    def action(self) -> int:
        return int(np.argmax(self.expected_action_utilities()))

    def channel_value(self, channel: InformationChannel) -> ChannelValue:
        h = np.asarray(channel.measurement_vector, dtype=float)
        if h.shape != self.mean.shape:
            raise ValueError("channel and state dimensions differ")
        predictive_variance = float(h @ self.covariance @ h + channel.noise_variance)
        if predictive_variance <= 0:
            improvement = 0.0
        else:
            kalman_gain = self.covariance @ h / predictive_variance
            current_value = float(np.max(self.expected_action_utilities()))
            posterior_value = 0.0
            # Predictive residual is Normal(0, predictive_variance).
            for node, weight in zip(self.nodes, self.weights):
                residual = np.sqrt(2.0 * predictive_variance) * node
                posterior_mean = self.mean + kalman_gain * residual
                posterior_value += float(weight) * float(np.max(self.expected_action_utilities(posterior_mean)))
            improvement = max(0.0, posterior_value - current_value)
        return ChannelValue(channel.name, improvement, channel.cost, improvement - channel.cost)

    def rank_channels(self) -> list[ChannelValue]:
        return sorted((self.channel_value(channel) for channel in self.channels), key=lambda item: item.net_value, reverse=True)

    def choose_channel(self) -> InformationChannel | None:
        ranked = self.rank_channels()
        if not ranked or ranked[0].net_value <= 0:
            return None
        chosen_name = ranked[0].name
        return next(channel for channel in self.channels if channel.name == chosen_name)

    def update(self, channel: InformationChannel, observation: float) -> None:
        h = np.asarray(channel.measurement_vector, dtype=float)
        if h.shape != self.mean.shape:
            raise ValueError("channel and state dimensions differ")
        predictive_variance = float(h @ self.covariance @ h + channel.noise_variance)
        if not np.isfinite(observation):
            raise ValueError("observation must be finite")
        if predictive_variance <= 0:
            if not np.isclose(observation, float(h @ self.mean), rtol=0, atol=1e-12):
                raise ValueError("observation contradicts a deterministic zero-variance belief")
            return
        gain = self.covariance @ h / predictive_variance
        residual = float(observation - h @ self.mean)
        self.mean = self.mean + gain * residual
        identity = np.eye(self.mean.size)
        # Joseph form keeps the covariance symmetric and positive under rounding.
        kh = np.outer(gain, h)
        self.covariance = (
            (identity - kh) @ self.covariance @ (identity - kh).T
            + channel.noise_variance * np.outer(gain, gain)
        )
        self.covariance = 0.5 * (self.covariance + self.covariance.T)

