import unittest

import numpy as np

from hmrm import HiddenModeResilienceMonitor, fit_transition


class HMRMTests(unittest.TestCase):
    def setUp(self):
        self.monitor = HiddenModeResilienceMonitor(0.04, 30, 0.005, 0.08)

    def test_scalar_cancellation_does_not_hide_loaded_slow_mode(self):
        result = self.monitor.assess(np.diag([0.5, 0.99]), np.array([-0.12, 0.12]), np.ones(2))
        self.assertFalse(result.scalar_only_alert)
        self.assertTrue(result.joint_alert)

    def test_inactive_slow_mode_does_not_trigger_joint_alarm(self):
        result = self.monitor.assess(np.diag([0.5, 0.99]), np.array([0.01, 0.001]), np.ones(2))
        self.assertTrue(result.recovery_only_alert)
        self.assertFalse(result.joint_alert)

    def test_transition_fit_recovers_known_dynamics(self):
        transition = np.array([[0.8, 0.1], [0.0, 0.96]])
        states = [np.array([0.3, -0.2])]
        for _ in range(80):
            states.append(transition @ states[-1])
        fitted = fit_transition(np.asarray(states), ridge=1e-12)
        np.testing.assert_allclose(fitted, transition, atol=1e-6)


if __name__ == "__main__":
    unittest.main()

