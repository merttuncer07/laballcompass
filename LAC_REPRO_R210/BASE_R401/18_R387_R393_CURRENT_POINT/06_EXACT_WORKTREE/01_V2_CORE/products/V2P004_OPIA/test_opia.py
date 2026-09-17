import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from opia import ObservationPolicyHistory, acquire_for_search_policy_with_backaction_guard

REPO = HERE.parents[2]
FOUNDRY_PRODUCTS = REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products"
if str(FOUNDRY_PRODUCTS) not in sys.path:
    sys.path.insert(0, str(FOUNDRY_PRODUCTS))
from P138_SPIA.parents.aicc import InformationChannel

P = [("local", 8, 0), ("intermittent", 2, 3)]
MEASUREMENT_CONTRAST = np.zeros(8); MEASUREMENT_CONTRAST[5] = 1; MEASUREMENT_CONTRAST[3] = -1
COVARIANCE = .0025 * np.outer(MEASUREMENT_CONTRAST, MEASUREMENT_CONTRAST)
CHANNELS = [InformationChannel("hotspot_contrast", MEASUREMENT_CONTRAST, .001, .02)]
EFFECT_CONTRAST = np.zeros(8); EFFECT_CONTRAST[7] = 1; EFFECT_CONTRAST[0] = -1


def near():
    return np.array([.12, 0, 0, .40, 0, .48, 0, 0])


def far():
    return np.array([.12, 0, 0, .70, 0, .18, 0, 0])


def history(beta=0.0, *, effect_contrast=EFFECT_CONTRAST, channel_name="hotspot_contrast"):
    # Observation is preferentially triggered in one latent-state region.  A naive
    # observed-vs-unobserved contrast is therefore confounded by state.  The
    # posterior-state adjustment recovers the declared observation effect beta.
    proxy = np.linspace(-1.0, 1.0, 81)
    observed = (proxy < 0).astype(int)
    grid = np.linspace(-1.0, 1.0, 9)
    p0 = .35 * grid + .03
    p1 = .35 * grid - .02
    posterior = np.empty_like(proxy)
    posterior[observed == 0] = np.interp(proxy[observed == 0], grid, p0)
    posterior[observed == 1] = np.interp(proxy[observed == 1], grid, p1)
    next_state = .1 + float(beta) * observed + .9 * posterior
    return ObservationPolicyHistory(
        channel_name=channel_name,
        passive_proxy=proxy,
        observed=observed,
        next_contrast_state=next_state,
        proxy_grid=grid,
        posterior_mean_if_unobserved=p0,
        posterior_mean_if_observed=p1,
        effect_contrast=np.asarray(effect_contrast, float),
    )


def run(mean, beta=0.0, *, covariance=COVARIANCE, channels=CHANNELS, effect_contrast=EFFECT_CONTRAST):
    hs={channels[0].name: history(beta, effect_contrast=effect_contrast, channel_name=channels[0].name)}
    return acquire_for_search_policy_with_backaction_guard(
        mean, covariance, policies=P, channels=channels, observation_histories=hs
    )


class P138InvariantPreservationTests(unittest.TestCase):
    def test_near_boundary_still_acquires_under_zero_backaction(self):
        r=run(near(), 0.0); self.assertEqual(r.chosen_channel, "hotspot_contrast")

    def test_far_boundary_still_skips_under_zero_backaction(self):
        r=run(far(), 0.0); self.assertIsNone(r.chosen_channel)

    def test_expected_time_is_linear_policy_utility(self):
        r=run(near(), 0.0); t=np.array(r.detection_time_vectors); e=t@near(); self.assertLess(abs(e[0]-e[1]),1e-12)

    def test_covariance_must_preserve_probability_sum(self):
        with self.assertRaises(ValueError): run(near(), 0.0, covariance=np.eye(8)*.01)

    def test_channel_must_be_contrast(self):
        bad=[InformationChannel("bad",np.ones(8),.1,0)]
        hs={"bad":history(0.0,channel_name="bad")}
        with self.assertRaises(ValueError):
            acquire_for_search_policy_with_backaction_guard(near(),COVARIANCE,policies=P,channels=bad,observation_histories=hs)

    def test_policy_vectors_cover_all_locations(self):
        r=run(near(),0.0); self.assertTrue(np.all(np.isfinite(r.detection_time_vectors)))


class K081ContrastiveCompositionTests(unittest.TestCase):
    def test_policy_adjustment_recovers_backaction_hidden_by_naive_difference(self):
        r=run(near(), .05)
        est=r.backaction_estimates[0]
        self.assertAlmostEqual(est["adjusted_coefficient"], .05, places=12)
        self.assertLess(est["naive_observed_minus_unobserved"], 0)

    def test_harmful_backaction_flips_acquisition_decision(self):
        r=run(near(), .05)
        self.assertEqual(r.base_chosen_channel,"hotspot_contrast")
        self.assertIsNone(r.chosen_channel)
        self.assertGreater(r.ranked_channels[0]["base_net_value"],0)
        self.assertLess(r.ranked_channels[0]["adjusted_net_value"],0)

    def test_estimated_shift_stays_in_simplex_tangent_space(self):
        r=run(near(), .05)
        shift=np.asarray(r.backaction_estimates[0]["belief_shift"])
        self.assertAlmostEqual(float(shift.sum()),0.0,places=12)
        shifted=near()+shift
        self.assertTrue(np.all(shifted>=0)); self.assertAlmostEqual(float(shifted.sum()),1.0,places=12)

    def test_non_tangent_effect_contrast_rejected(self):
        bad=np.ones(8)
        with self.assertRaises(ValueError): run(near(),.05,effect_contrast=bad)

    def test_missing_channel_model_fails_closed(self):
        with self.assertRaises(ValueError):
            acquire_for_search_policy_with_backaction_guard(near(),COVARIANCE,policies=P,channels=CHANNELS,observation_histories={})

    def test_zero_backaction_preserves_base_net_value(self):
        r=run(near(),0.0)
        self.assertAlmostEqual(r.ranked_channels[0]["adjusted_net_value"],r.ranked_channels[0]["base_net_value"],places=12)

    def test_zero_variance_zero_backaction_preserves_base_net_value(self):
        channel=[InformationChannel("hotspot_contrast",MEASUREMENT_CONTRAST,0.0,.02)]
        r=run(near(),0.0,covariance=np.zeros((8,8)),channels=channel)
        self.assertAlmostEqual(r.ranked_channels[0]["adjusted_net_value"],r.ranked_channels[0]["base_net_value"],places=12)


if __name__ == "__main__":
    unittest.main()
