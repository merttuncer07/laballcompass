import unittest

import numpy as np

from adaptive_metric import (
    AdaptationConfig,
    adaptive_compiled_sequence,
    compound_correlation,
    correlation_retraction,
    fixed_metric_sequence,
    signed_rank_one_correlation,
    theoretical_raw_moment,
    update_with_metric,
)
from automatic_psd_closure import compile_closure, observation


class AdaptiveMetricTests(unittest.TestCase):
    def test_correlation_families_are_psd_and_unit_diagonal(self):
        for matrix in (
            compound_correlation(8, 0.32),
            compound_correlation(8, -0.10),
            signed_rank_one_correlation(8, 0.42),
        ):
            self.assertTrue(np.allclose(np.diag(matrix), 1.0))
            self.assertGreater(np.min(np.linalg.eigvalsh(matrix)), -1e-10)

    def test_retraction_is_positive_definite_correlation(self):
        rng = np.random.default_rng(31)
        raw = rng.normal(size=(6, 6))
        raw = raw + raw.T
        result = correlation_retraction(raw, 0.8)
        self.assertTrue(np.allclose(np.diag(result), 1.0))
        self.assertGreater(np.min(np.linalg.eigvalsh(result)), 0.0)

    def test_residual_moment_recovers_population_correlation(self):
        rng = np.random.default_rng(44)
        truth = signed_rank_one_correlation(6, 0.35)
        state_covariance = 0.4 * np.eye(6) + 0.08 * np.ones((6, 6))
        raw = theoretical_raw_moment(
            rng, truth, state_covariance, count=120_000
        )
        estimated = correlation_retraction(raw, 1.0)
        self.assertLess(np.sqrt(np.mean((estimated - truth) ** 2)), 0.018)

    def test_fixed_general_metric_update_is_finite_and_psd(self):
        closure, _ = compile_closure(
            4, "gaussian", training_count=3_000, calibration_trajectories=0
        )
        rng = np.random.default_rng(9)
        measured = observation(rng.normal(size=(3, 5, 4)), 0.16)
        transition = 0.8 * np.eye(4)
        metric = closure.noise_variance * compound_correlation(4, 0.3)
        estimate, covariance = fixed_metric_sequence(
            closure, measured, transition, 0.28, 0.16, metric
        )
        self.assertTrue(np.all(np.isfinite(estimate)))
        self.assertGreater(np.min(np.linalg.eigvalsh(covariance)), 0.0)

    def test_adaptive_metric_is_causal_finite_and_psd(self):
        closure, _ = compile_closure(
            4, "gaussian", training_count=3_000, calibration_trajectories=0
        )
        rng = np.random.default_rng(19)
        measured = observation(rng.normal(size=(3, 8, 4)), 0.16)
        estimate, covariance, correlation, diagnostics = adaptive_compiled_sequence(
            closure,
            measured,
            0.8 * np.eye(4),
            0.28,
            0.16,
            AdaptationConfig("full", gain=0.1, shrinkage=0.7),
        )
        self.assertTrue(np.all(np.isfinite(estimate)))
        self.assertGreater(np.min(np.linalg.eigvalsh(covariance)), 0.0)
        self.assertTrue(np.allclose(correlation[:, 0], np.eye(4)))
        self.assertIn("fraction_bounded_ray", diagnostics)

    def test_bounded_ray_prevents_extreme_cubic_overshoot(self):
        closure, _ = compile_closure(
            4, "gaussian", training_count=3_000, calibration_trajectories=0
        )
        mean = np.zeros((1, 4))
        covariance = np.eye(4)[None]
        measured = np.array([[35.0, 0.2, -0.1, 0.3]])
        metric = closure.noise_variance * np.eye(4)
        unsafe = update_with_metric(
            closure,
            mean,
            covariance,
            measured,
            0.45,
            metric,
            support_gate=False,
        )
        safe = update_with_metric(
            closure,
            mean,
            covariance,
            measured,
            0.45,
            metric,
            support_gate=True,
        )
        self.assertLess(np.linalg.norm(safe[0]), np.linalg.norm(unsafe[0]))
        self.assertLess(safe[5][0], 1.0)
        self.assertTrue(np.all(np.isfinite(safe[0])))


if __name__ == "__main__":
    unittest.main()
