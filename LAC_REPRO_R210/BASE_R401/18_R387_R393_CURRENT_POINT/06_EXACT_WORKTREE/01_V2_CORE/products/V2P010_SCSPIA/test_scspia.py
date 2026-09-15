import unittest
import numpy as np

from scspia import (
    InformationChannel,
    acquire_for_search_policy,
    simplex_tangent_basis,
    support_calibrated_search_policy_acquisition,
)

P = [('local', 8, 0), ('intermittent', 2, 3)]
NEAR = np.array([.12, 0, 0, .40, 0, .48, 0, 0], float)


def construction(seed=1, ntrain=12):
    rng = np.random.default_rng(seed)
    B = simplex_tangent_basis(8)
    variances = np.exp(rng.uniform(np.log(0.0002), np.log(0.006), 7))
    Ctrue_z = np.diag(variances)
    Ctrue = B @ Ctrue_z @ B.T
    uniform = np.ones(8) / 8
    Z = rng.multivariate_normal(np.zeros(7), Ctrue_z, size=ntrain)
    X = uniform + Z @ B.T
    assert np.min(X) >= 0
    channels = [InformationChannel(f'c{j}', B[:, j], .0004, .002) for j in range(7)]
    return B, variances, Ctrue, X, channels


class SCSPIATests(unittest.TestCase):
    def test_lifted_covariance_is_simplex_tangent(self):
        B, _, _, X, ch = construction()
        r = support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch, shrinkage_grid=[0.0])
        C = np.array(r.covariance)
        self.assertLess(np.max(np.abs(C.sum(axis=0))), 1e-10)
        self.assertLess(r.simplex_tangent_residual, 1e-10)

    def test_declared_tangent_support_is_exact(self):
        B, _, _, X, ch = construction()
        r = support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch, shrinkage_grid=[0.0])
        Cz = B.T @ np.array(r.covariance) @ B
        off = Cz - np.diag(np.diag(Cz))
        self.assertLess(np.max(np.abs(off)), 1e-10)
        self.assertEqual(r.tangent_unsupported_max_absolute_covariance, 0.0)

    def test_covariance_is_psd_on_tangent_space(self):
        B, _, _, X, ch = construction()
        r = support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch, shrinkage_grid=[0.0])
        self.assertGreater(r.tangent_minimum_eigenvalue, 0)

    def test_seed_one_recovers_oracle_channel_while_raw_sample_does_not(self):
        _, _, Ctrue, X, ch = construction(seed=1)
        oracle = acquire_for_search_policy(NEAR, Ctrue, policies=P, channels=ch)
        raw = acquire_for_search_policy(NEAR, np.cov(X, rowvar=False, ddof=1), policies=P, channels=ch)
        structured = support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch, shrinkage_grid=[0.0])
        self.assertEqual(oracle.chosen_channel, 'c6')
        self.assertEqual(structured.chosen_channel, oracle.chosen_channel)
        self.assertNotEqual(raw.chosen_channel, oracle.chosen_channel)

    def test_result_exposes_ranked_channels(self):
        _, _, _, X, ch = construction()
        r = support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch, shrinkage_grid=[0.0])
        self.assertEqual(len(r.ranked_channels), 7)
        self.assertEqual(r.ranked_channels[0]['name'], r.chosen_channel)

    def test_holdout_calibration_path_runs(self):
        _, _, _, X, ch = construction(ntrain=20)
        r = support_calibrated_search_policy_acquisition(X[:12], np.eye(7, dtype=bool), NEAR, policies=P, channels=ch, holdout_beliefs=X[12:], shrinkage_grid=[0.0, .25, .5, .75, 1.0])
        self.assertIn(r.selected_shrinkage, {0.0, .25, .5, .75, 1.0})

    def test_negative_probability_rejected(self):
        _, _, _, X, ch = construction(); bad = X.copy(); bad[0,0] = -0.1; bad[0,1] += 0.1
        with self.assertRaises(ValueError):
            support_calibrated_search_policy_acquisition(bad, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch)

    def test_nonunit_row_sum_rejected(self):
        _, _, _, X, ch = construction(); bad = X.copy(); bad[0,0] += .01
        with self.assertRaises(ValueError):
            support_calibrated_search_policy_acquisition(bad, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch)

    def test_bad_support_shape_rejected(self):
        _, _, _, X, ch = construction()
        with self.assertRaises(ValueError):
            support_calibrated_search_policy_acquisition(X, np.eye(8, dtype=bool), NEAR, policies=P, channels=ch)

    def test_bad_current_belief_rejected(self):
        _, _, _, X, ch = construction()
        with self.assertRaises(ValueError):
            support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), np.ones(8), policies=P, channels=ch)

    def test_noncontrast_channel_still_fails_p138_contract(self):
        _, _, _, X, _ = construction(); bad = [InformationChannel('bad', np.ones(8), .01, 0.0)]
        with self.assertRaises(ValueError):
            support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), NEAR, policies=P, channels=bad)

    def test_condition_number_is_finite(self):
        _, _, _, X, ch = construction()
        r = support_calibrated_search_policy_acquisition(X, np.eye(7, dtype=bool), NEAR, policies=P, channels=ch, shrinkage_grid=[0.0])
        self.assertTrue(np.isfinite(r.tangent_condition_number))


if __name__ == '__main__': unittest.main()
