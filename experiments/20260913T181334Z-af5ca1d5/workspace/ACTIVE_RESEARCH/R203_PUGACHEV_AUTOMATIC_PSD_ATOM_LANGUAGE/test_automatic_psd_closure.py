import unittest

import numpy as np

from automatic_psd_closure import (
    compile_closure,
    observation,
    jacobian,
)


class AutomaticPSDClosureTests(unittest.TestCase):
    def test_jacobian_matches_finite_difference(self):
        rng = np.random.default_rng(9)
        state = rng.normal(size=(3, 4))
        analytic = jacobian(state, 0.16)
        epsilon = 1e-6
        numerical = np.empty_like(analytic)
        for coordinate in range(4):
            step = np.zeros_like(state)
            step[:, coordinate] = epsilon
            numerical[:, :, coordinate] = (
                observation(state + step, 0.16)
                - observation(state - step, 0.16)
            ) / (2.0 * epsilon)
        self.assertTrue(np.allclose(analytic, numerical, atol=2e-6))

    def test_automatic_atoms_are_psd_and_subexponential(self):
        closure, record = compile_closure(
            4,
            "mixture",
            training_count=4_000,
            calibration_trajectories=0,
        )
        self.assertEqual(record["atom_count"], 12)
        self.assertLess(record["atom_count"], record["cartesian_10bin_atom_count"])
        self.assertGreater(np.min(np.linalg.eigvalsh(closure.covariance_atoms)), 0.0)

    def test_eight_dimensional_update_is_finite_and_psd(self):
        closure, _ = compile_closure(
            8,
            "gaussian",
            training_count=4_000,
            calibration_trajectories=0,
        )
        rng = np.random.default_rng(31)
        mean = rng.normal(scale=0.2, size=(5, 8))
        covariance = np.repeat(np.eye(8)[None, :, :], 5, axis=0)
        measured = observation(mean, 0.16) + rng.normal(scale=0.28, size=mean.shape)
        posterior_mean, posterior_covariance = closure.update(
            mean, covariance, measured, 0.16
        )
        self.assertTrue(np.all(np.isfinite(posterior_mean)))
        self.assertTrue(np.all(np.isfinite(posterior_covariance)))
        self.assertGreater(np.min(np.linalg.eigvalsh(posterior_covariance)), 0.0)


if __name__ == "__main__":
    unittest.main()
