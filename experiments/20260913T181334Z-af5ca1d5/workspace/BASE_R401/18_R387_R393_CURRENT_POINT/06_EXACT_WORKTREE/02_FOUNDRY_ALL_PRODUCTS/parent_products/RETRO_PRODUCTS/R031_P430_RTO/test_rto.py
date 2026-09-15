import unittest

import numpy as np

from rto import evaluate_restart_threshold, optimize_restart_threshold


class RTOTests(unittest.TestCase):
    def test_two_point_formula(self):
        policy = evaluate_restart_threshold(np.array([1.0, 100.0]), 2.0, restart_overhead=1.0)
        self.assertAlmostEqual(policy.expected_completion_time, 4.0)
        self.assertAlmostEqual(policy.expected_failed_attempts, 1.0)

    def test_no_success_before_threshold_is_infeasible(self):
        policy = evaluate_restart_threshold(np.array([5.0, 6.0]), 4.0)
        self.assertTrue(np.isinf(policy.expected_completion_time))

    def test_deterministic_completion_selects_no_restart(self):
        policy = optimize_restart_threshold(np.full(100, 10.0), restart_overhead=1.0)
        self.assertIsNone(policy.threshold)

    def test_heavy_tail_can_benefit_from_restart(self):
        samples = np.concatenate([np.full(90, 2.0), np.full(10, 100.0)])
        policy = optimize_restart_threshold(samples, restart_overhead=0.5)
        self.assertIsNotNone(policy.threshold)
        self.assertGreater(policy.improvement_vs_no_restart, 0.5)


if __name__ == "__main__":
    unittest.main()

