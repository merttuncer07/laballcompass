import unittest

import numpy as np

from dfdpe import estimate_affine_dynamics, simulate_affine_dynamics


def construction(seed=14, noise=.20):
    rng = np.random.default_rng(seed)
    times = np.linspace(0, 40, 801)
    inputs = .7 * np.sin(.63 * times) + .35 * np.sin(1.71 * times) + (times > 17) * .45
    truth = np.array([-.42, 1.35, .22])
    clean = simulate_affine_dynamics(times, inputs, 1.7, truth)
    observed = clean + rng.normal(scale=noise, size=clean.size)
    validation_times = np.linspace(0, 18, 361)
    validation_inputs = .5 * np.cos(.47 * validation_times) - .4 * np.sin(1.23 * validation_times)
    validation_clean = simulate_affine_dynamics(validation_times, validation_inputs, -.8, truth)
    return times, observed, inputs, validation_times, validation_clean, validation_inputs, truth


class Tests(unittest.TestCase):
    def test_clean_signal_recovers_parameters_without_derivative(self):
        values = construction(noise=0)
        result = estimate_affine_dynamics(*values[:3], window_duration=4, window_step=.5)
        estimate = np.array([result.estimate.persistence, result.estimate.input_gain, result.estimate.drift])
        self.assertLess(np.max(np.abs(estimate - values[-1])), .015)
        self.assertFalse(result.derivative_taken_from_observed_data)

    def test_noisy_estimate_is_useful_on_untouched_rollout(self):
        t, y, u, vt, vy, vu, _ = construction()
        result = estimate_affine_dynamics(
            t, y, u, window_duration=4, window_step=.5,
            validation_times=vt, validation_outputs=vy, validation_inputs=vu,
        )
        self.assertEqual(result.status, "DYNAMIC_PARAMETERS_ESTIMATED_WITHOUT_DATA_DIFFERENTIATION")
        self.assertLess(result.estimate.validation_rollout_rmse, .08)
        self.assertLess(result.estimate.validation_rollout_rmse, result.finite_difference_baseline.validation_rollout_rmse)

    def test_underexcited_data_is_preserved_as_nonidentifiable(self):
        times = np.linspace(0, 10, 201)
        result = estimate_affine_dynamics(
            times, np.ones_like(times) * 2, np.ones_like(times),
            window_duration=2, window_step=.5,
        )
        self.assertIsNone(result.estimate)
        self.assertEqual(result.status, "UNDEREXCITED_PARAMETERS_NOT_IDENTIFIABLE")

    def test_partial_validation_data_is_rejected(self):
        t, y, u, vt, vy, _, _ = construction()
        with self.assertRaises(ValueError):
            estimate_affine_dynamics(
                t, y, u, window_duration=4, window_step=.5,
                validation_times=vt, validation_outputs=vy,
            )


if __name__ == "__main__":
    unittest.main()
