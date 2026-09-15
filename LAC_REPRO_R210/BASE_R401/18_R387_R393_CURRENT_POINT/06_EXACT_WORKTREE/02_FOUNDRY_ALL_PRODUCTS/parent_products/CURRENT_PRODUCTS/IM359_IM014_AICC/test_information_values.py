import unittest
import math
import numpy as np
from scipy.integrate import quad
from aicc import AdaptiveInformationController, InformationChannel, affine_information_value


def controller(channels, noise=None, **kwargs):
    return AdaptiveInformationController(np.zeros(1), np.eye(1), np.array([[0.], [1.]]),
        np.zeros(2), channels, channel_noise_covariance=noise,
        covariance_channel_names=[c.name for c in channels] if noise is not None else None, **kwargs)


class ExactValueTests(unittest.TestCase):
    def test_cost_boundary_rejected_by_old_31_node_quadrature(self):
        c = InformationChannel('measure', np.ones(1), 0., .393)
        ctl = controller([c])
        self.assertAlmostEqual(ctl.channel_value(c).expected_decision_improvement, 1/math.sqrt(2*math.pi), places=14)
        self.assertEqual(ctl.choose_channel().name, 'measure')

    def test_quadrature_parameter_no_longer_changes_decision(self):
        c = InformationChannel('measure', np.ones(1), 0., .393)
        values = [controller([c], quadrature_points=n).channel_value(c).net_value for n in (2, 3, 31, 100)]
        self.assertEqual(len(set(values)), 1)

    def test_duplicate_dominated_and_common_slope_invariance(self):
        expected = 1/math.sqrt(2*math.pi)
        self.assertAlmostEqual(affine_information_value([0, 0, -4, 0], [0, 1, 1, 0]), expected, places=14)
        self.assertAlmostEqual(affine_information_value([7, 7, 3, 7], [20, 21, 21, 20]), expected, places=14)
        self.assertEqual(affine_information_value([1, 2, 3], [5, 5, 5]), 0.)

    def test_random_actions_against_independent_piecewise_numerical_integration(self):
        rng = np.random.default_rng(9184)
        for _ in range(24):
            a, b = rng.normal(size=(2, 7))
            # All pair crossings, including dominated lines: independent of
            # the production upper-envelope construction.
            cuts = sorted({-12., 12.} | {(a[j]-a[i])/(b[i]-b[j]) for i in range(7) for j in range(i)
                          if b[i] != b[j] and -12 < (a[j]-a[i])/(b[i]-b[j]) < 12})
            baseline = max(a)
            value = sum(quad(lambda z: (max(a+b*z)-baseline)*math.exp(-z*z/2)/math.sqrt(2*math.pi), lo, hi,
                             epsabs=1e-12)[0] for lo, hi in zip(cuts, cuts[1:]))
            self.assertAlmostEqual(affine_information_value(a, b), value, places=10)

    def test_small_positive_tail_does_not_cancel_to_zero(self):
        for x in (8., 12., 25.):
            reference = quad(lambda z: (z-x)*math.exp(-z*z/2)/math.sqrt(2*math.pi), x, x+8,
                             epsabs=1e-155, epsrel=1e-10)[0]
            actual = affine_information_value([0., -x], [0., 1.])
            self.assertGreater(actual, 0.)
            self.assertAlmostEqual(actual/reference, 1., places=9)


class JointObservationTests(unittest.TestCase):
    def channels(self, count=2):
        return [InformationChannel(str(i), np.ones(1), 1.) for i in range(count)]

    def test_perfect_alias_does_not_gain_information_or_shift_belief(self):
        channels = self.channels(3)
        ctl = controller(channels, np.array([[1, 1, 0], [1, 1, 0], [0, 0, 1.]]))
        ctl.update(channels[0], 1.)
        self.assertEqual(ctl.channel_value(channels[1]).expected_decision_improvement, 0.)
        self.assertEqual(ctl.choose_channel().name, '2')
        ctl.update(channels[1], 1.)
        np.testing.assert_allclose(ctl.mean, [.5], atol=1e-14)
        np.testing.assert_allclose(ctl.covariance, [[.5]], atol=1e-14)
        ctl.update(channels[2], 1.)
        np.testing.assert_allclose(ctl.covariance, [[1/3]], atol=1e-14)

    def test_distinct_independent_equal_values_are_not_merged(self):
        channels = self.channels()
        ctl = controller(channels, np.eye(2))
        for c in channels: ctl.update(c, 1.)
        np.testing.assert_allclose(ctl.mean, [2/3], atol=1e-14)
        np.testing.assert_allclose(ctl.covariance, [[1/3]], atol=1e-14)

    def test_repeated_finite_observation_is_idempotent_but_default_is_fresh(self):
        c = self.channels(1)[0]
        for noise, expected in ((np.eye(1), .5), (None, 1/3)):
            ctl = controller([c], noise)
            ctl.update(c, 1.); ctl.update(c, 1.)
            self.assertAlmostEqual(ctl.covariance[0, 0], expected, places=13)

    def test_partial_noise_dependence_matches_batch_conditioning_in_any_order(self):
        channels = self.channels()
        r = np.array([[1, .8], [.8, 1.]])
        cross = np.ones((1, 2)); predictive = np.ones((2, 2))+r
        y = np.array([1., .6])
        expected_mean = cross@np.linalg.solve(predictive, y)
        expected_cov = np.eye(1)-cross@np.linalg.solve(predictive, cross.T)
        for order in ((0, 1), (1, 0)):
            ctl = controller(channels, r)
            for i in order: ctl.update(channels[i], y[i])
            np.testing.assert_allclose(ctl.mean, expected_mean, atol=1e-13)
            np.testing.assert_allclose(ctl.covariance, expected_cov, atol=1e-13)

    def test_remaining_channel_value_uses_conditional_noise_and_predictive_mean(self):
        channels = self.channels()
        ctl = controller(channels, np.array([[1, .8], [.8, 1.]]))
        ctl.update(channels[0], 1.)
        mu, variance, cross, _ = ctl._predict(channels[1])
        self.assertAlmostEqual(mu, .9, places=13)
        self.assertAlmostEqual(variance, .38, places=13)
        self.assertAlmostEqual(cross[0], .1, places=13)
        scale = .1/math.sqrt(.38)
        reference = quad(lambda z: (max(0., .5+scale*z)-.5)*math.exp(-z*z/2)/math.sqrt(2*math.pi),
                         -12, 12, points=[-.5/scale], epsabs=1e-12)[0]
        self.assertAlmostEqual(ctl.channel_value(channels[1]).expected_decision_improvement, reference, places=12)

    def test_opposite_common_error_cancels_and_identifies_state(self):
        channels = self.channels()
        ctl = controller(channels, np.array([[1, -1], [-1, 1.]]))
        ctl.update(channels[0], .1); ctl.update(channels[1], .7)
        np.testing.assert_allclose(ctl.mean, [.4], atol=1e-14)
        self.assertLess(ctl.covariance[0, 0], 1e-27)

    def test_conflicting_repeat_rejected_without_state_mutation(self):
        channels = self.channels()
        ctl = controller(channels, np.ones((2, 2)))
        ctl.update(channels[0], 1.)
        before = ctl.mean.copy(), ctl.covariance.copy()
        with self.assertRaisesRegex(ValueError, 'contradicts'): ctl.update(channels[1], 2.)
        np.testing.assert_array_equal(ctl.mean, before[0]); np.testing.assert_array_equal(ctl.covariance, before[1])

    def test_joint_model_validation(self):
        channels = self.channels()
        for noise in (np.array([[1, 2], [2, 1]]), np.eye(2)*2, np.array([[1, .2], [.8, 1]])):
            with self.assertRaises(ValueError): controller(channels, noise)
        with self.assertRaisesRegex(ValueError, 'order'):
            AdaptiveInformationController([0], [[1]], [[0], [1]], [0, 0], channels,
                                          channel_noise_covariance=np.eye(2), covariance_channel_names=['1', '0'])
        ctl = controller(channels, np.eye(2))
        with self.assertRaisesRegex(ValueError, 'definition'):
            ctl.channel_value(InformationChannel('0', np.array([2.]), 1.))

    def test_multidimensional_joint_matches_direct_batch_reference(self):
        rng = np.random.default_rng(3781)
        p0 = rng.normal(size=(3, 3)); p = p0@p0.T
        r0 = rng.normal(size=(4, 4)); r = r0@r0.T + .2*np.eye(4)
        h = rng.normal(size=(4, 3)); mu = rng.normal(size=3); y = rng.normal(size=4)
        channels = [InformationChannel(str(i), h[i], r[i, i]) for i in range(4)]
        cross = p@h.T; pred = h@p@h.T+r
        expected_mean = mu+cross@np.linalg.solve(pred, y-h@mu)
        expected_cov = p-cross@np.linalg.solve(pred, cross.T)
        for order in ((0, 1, 2, 3), (3, 1, 0, 2)):
            ctl = AdaptiveInformationController(mu, p, [[0, 0, 0], [1, 0, 0]], [0, 0], channels,
                    channel_noise_covariance=r, covariance_channel_names=[c.name for c in channels])
            for i in order: ctl.update(channels[i], y[i])
            np.testing.assert_allclose(ctl.mean, expected_mean, atol=1e-12)
            np.testing.assert_allclose(ctl.covariance, expected_cov, atol=1e-12)


if __name__ == '__main__': unittest.main()
