"""Adaptive Information-Channel Controller (AICC)."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


def affine_information_value(intercepts, slopes) -> float:
    """E[max_i(a_i+b_i Z)]-max_i(a_i), Z~N(0,1), via its upper envelope.

    Implements the known Gaussian knowledge-gradient identity, not a new
    acquisition rule. Reference: Frazier, Powell & Dayanik (2009), and their
    INFORMSJoC/1080.0314 ckg/LogEmaxAffine.m and AffineBreakpoints.m.
    No fixed-node quadrature: breakpoints explicitly capture decision changes.
    """
    a, b = np.asarray(intercepts, dtype=float), np.asarray(slopes, dtype=float)
    if a.ndim != 1 or not a.size or b.shape != a.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError('finite, nonempty, matching affine utility vectors required')
    best = {}
    for ai, bi in zip(a, b):
        best[float(bi)] = max(best.get(float(bi), -math.inf), float(ai))
    hull, starts = [], []
    for bi, ai in sorted(best.items()):
        crossing = -math.inf
        while hull:
            bj, aj = hull[-1]
            crossing = (aj-ai)/(bi-bj)
            if len(hull) == 1 or crossing > starts[-1]: break
            hull.pop(); starts.pop()
        hull.append((bi, ai)); starts.append(crossing)
    terms = []
    for i in range(1, len(hull)):
        x = abs(starts[i])
        if not math.isfinite(x): continue
        density = math.exp(-.5*x*x)/math.sqrt(2*math.pi)
        if x <= 10:
            tail_value = density - x*.5*math.erfc(x/math.sqrt(2))
        else:
            # Asymptotic normal-loss series avoids subtracting almost equal
            # tail terms. Stop at convergence or the least term.
            inv = 1/(x*x); term = total = inv
            for k in range(1, 100):
                following = term * (-(2*k+1)*inv)
                if abs(following) >= abs(term): break
                total += following
                if abs(following) < abs(total)*1e-16: break
                term = following
            tail_value = density*total
        terms.append((hull[i][0]-hull[i-1][0])*max(0., tail_value))
    value = math.fsum(terms)
    if not math.isfinite(value): raise ValueError('utility scale overflows floating-point information value')
    return value


def _psd_factor(matrix, label):
    """Square-root factor without adding fictitious independent noise."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not np.all(np.isfinite(matrix)):
        raise ValueError(label+' must be a finite square matrix')
    scale = float(np.max(np.abs(matrix), initial=0.))
    if scale == 0: return np.zeros_like(matrix)
    normalized = matrix/scale
    if not np.allclose(normalized, normalized.T, rtol=0, atol=1e-12):
        raise ValueError(label+' must be symmetric')
    values, vectors = np.linalg.eigh((normalized+normalized.T)*.5)
    if values.min(initial=0.) < -1e-12:
        raise ValueError(label+' must be positive semidefinite')
    return vectors*np.sqrt(np.maximum(values, 0.)*scale)


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
    """One-step Gaussian information selection with affine action utilities.

    Default: each update is a fresh independent noise draw. To represent a
    finite set of potentially overlapping observations, supply the named joint
    channel noise covariance. In that mode a channel denotes one observation,
    so repeating it cannot add information. Noise is initially independent of
    the latent state. Neither mode infers dependence from matching numbers.
    """

    def __init__(
        self,
        belief_mean: np.ndarray,
        belief_covariance: np.ndarray,
        action_slopes: np.ndarray,
        action_intercepts: np.ndarray,
        channels: list[InformationChannel],
        quadrature_points: int = 31,
        *,
        channel_noise_covariance: np.ndarray | None = None,
        covariance_channel_names: list[str] | None = None,
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
        # Retained for call compatibility; exact affine integration has no grid.
        if self.action_slopes.shape[1] != self.mean.size:
            raise ValueError("action and state dimensions differ")
        self.information_mode = 'fresh_independent_measurements'
        self._joint_factor = None
        if channel_noise_covariance is None:
            if covariance_channel_names is not None:
                raise ValueError('covariance_channel_names requires channel_noise_covariance')
        else:
            m = len(self.channels)
            if not m or m+d > 1000:
                raise ValueError('finite joint observation model requires channels and at most 1000 combined dimensions')
            if list(covariance_channel_names or []) != [c.name for c in self.channels]:
                raise ValueError('covariance_channel_names must match offered channel order exactly')
            noise = np.asarray(channel_noise_covariance, dtype=float)
            if noise.shape != (m, m): raise ValueError('channel noise covariance dimensions differ')
            noise_factor = _psd_factor(noise, 'channel noise covariance')
            variances = np.array([c.noise_variance for c in self.channels])
            if not np.allclose(np.diag(noise), variances, rtol=1e-10, atol=0):
                raise ValueError('channel noise covariance diagonal must match channel noise_variance')
            state_factor = _psd_factor(self.covariance, 'belief covariance')
            h = np.vstack([c.measurement_vector for c in self.channels])
            self._joint_factor = np.block([[state_factor, np.zeros((d, m))], [h@state_factor, noise_factor]])
            self._joint_mean = np.concatenate([self.mean, h@self.mean])
            self._initial_joint_variances = np.sum(self._joint_factor**2, axis=1)
            self._channel_indices = {c.name: d+i for i, c in enumerate(self.channels)}
            self.information_mode = 'finite_joint_observations'

    def _predict(self, channel):
        h = np.asarray(channel.measurement_vector, dtype=float)
        if h.shape != self.mean.shape:
            raise ValueError('channel and state dimensions differ')
        if self._joint_factor is None:
            return float(h@self.mean), float(h@self.covariance@h+channel.noise_variance), self.covariance@h, None
        index = self._channel_indices.get(channel.name)
        if index is None: raise ValueError('channel not in finite joint observation model')
        original = self.channels[index-self.mean.size]
        if not np.array_equal(h, original.measurement_vector) or channel.noise_variance != original.noise_variance:
            raise ValueError('channel definition differs from finite joint observation model')
        row = self._joint_factor[index]
        variance = float(row@row)
        tolerance = (64*np.finfo(float).eps)**2*self._initial_joint_variances[index]
        if variance <= tolerance: variance = 0.
        cross = self._joint_factor[:self.mean.size]@row
        return float(self._joint_mean[index]), variance, cross, index

    def expected_action_utilities(self, mean: np.ndarray | None = None) -> np.ndarray:
        location = self.mean if mean is None else np.asarray(mean, dtype=float)
        return self.action_slopes @ location + self.action_intercepts

    def action(self) -> int:
        return int(np.argmax(self.expected_action_utilities()))

    def channel_value(self, channel: InformationChannel) -> ChannelValue:
        _, predictive_variance, cross, _ = self._predict(channel)
        if predictive_variance <= 0:
            improvement = 0.0
        else:
            improvement = affine_information_value(self.expected_action_utilities(), self.action_slopes@cross/np.sqrt(predictive_variance))
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
        predicted_mean, predictive_variance, cross, index = self._predict(channel)
        if not np.isfinite(observation):
            raise ValueError("observation must be finite")
        if predictive_variance <= 0:
            tolerance = max(1e-12, 64*np.finfo(float).eps*max(abs(observation), abs(predicted_mean))) if index is not None else 1e-12
            if not np.isclose(observation, predicted_mean, rtol=0, atol=tolerance):
                raise ValueError("observation contradicts a deterministic zero-variance belief")
            return
        residual = float(observation - predicted_mean)
        if index is not None:
            # Condition the augmented [state, finite observations] Gaussian by
            # projecting its square root. Avoid a covariance subtraction that
            # could turn a perfect duplicate into spurious residual variance.
            direction = self._joint_factor[index]/np.sqrt(predictive_variance)
            projection = self._joint_factor@direction
            self._joint_mean += projection*(residual/np.sqrt(predictive_variance))
            self._joint_factor -= np.outer(projection, direction)
            self._joint_factor[index] = 0.
            self._joint_mean[index] = observation
            self.mean = self._joint_mean[:self.mean.size].copy()
            state_factor = self._joint_factor[:self.mean.size]
            self.covariance = state_factor@state_factor.T
            return
        gain = cross / predictive_variance
        self.mean = self.mean + gain * residual
        identity = np.eye(self.mean.size)
        # Joseph form keeps the covariance symmetric and positive under rounding.
        kh = np.outer(gain, h)
        self.covariance = (
            (identity - kh) @ self.covariance @ (identity - kh).T
            + channel.noise_variance * np.outer(gain, gain)
        )
        self.covariance = 0.5 * (self.covariance + self.covariance.T)


def run_information_sequence(config):
    """Rank information before/after supplied observations; never invent data."""
    from dataclasses import asdict
    channels = [InformationChannel(c['name'], np.asarray(c['measurement_vector'], dtype=float),
                                   c['noise_variance'], c.get('cost', 0.)) for c in config['channels']]
    controller = AdaptiveInformationController(config['belief_mean'], config['belief_covariance'],
        config['action_slopes'], config['action_intercepts'], channels,
        channel_noise_covariance=config.get('channel_noise_covariance'),
        covariance_channel_names=config.get('covariance_channel_names'))
    def state():
        ranked = controller.rank_channels()
        return {'mean': controller.mean.tolist(), 'covariance': controller.covariance.tolist(),
                'action_index': controller.action(), 'ranked_channels': [asdict(v) for v in ranked],
                'chosen_channel': ranked[0].name if ranked and ranked[0].net_value > 0 else None}
    result = {'information_mode': controller.information_mode, 'initial': state(), 'steps': [],
              'value_method': 'Gaussian affine upper-envelope integration',
              'scope': 'One-step expected value under supplied Gaussian belief, affine utilities and costs on the same utility scale. Finite joint mode models one observation per channel, with supplied noise covariance initially independent of the state. Default mode treats each update as a fresh independent noise draw. No inferred covariance, audit probability, or globally optimal multi-step policy.'}
    lookup = {c.name: c for c in channels}
    for event in config.get('observations', []):
        if event['channel'] not in lookup: raise ValueError('unknown observation channel')
        controller.update(lookup[event['channel']], event['value'])
        result['steps'].append({'observation': dict(event), **state()})
    return result


if __name__ == '__main__':
    import argparse
    import hashlib
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='AICC: rank Gaussian measurements and condition on supplied observations')
    parser.add_argument('input'); parser.add_argument('--output')
    args = parser.parse_args()
    try:
        source = Path(args.input)
        raw = source.read_bytes()
        result = run_information_sequence(json.loads(raw))
        result['input_sha256'] = hashlib.sha256(raw).hexdigest()
        result['engine_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if args.output:
            with Path(args.output).open('x') as handle: json.dump(result, handle, indent=2, allow_nan=False)
            print(args.output)
        else: print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.error(str(error))
