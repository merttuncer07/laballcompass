import unittest

import numpy as np

from ispo import evaluate_periodic_policy, optimize_search_policy


class Tests(unittest.TestCase):
    def test_intermitttent_policy_connects_distant_hotspots(self):
        probabilities = np.zeros(120)
        probabilities[:5] = 0.1
        probabilities[60:65] = 0.1
        result = optimize_search_policy(
            probabilities, [1, 2, 5, 10], [0, 16, 35, 55, 59],
            relocation_speed=40.0, relocation_overhead=0.25,
        )
        self.assertTrue(result.selected.feasible)
        self.assertGreater(result.selected.relocation_jump, 0)
        self.assertGreater(result.expected_time_improvement_fraction, 0.5)

    def test_uniform_support_preserves_complete_coverage(self):
        probabilities = np.ones(20)
        result = optimize_search_policy(probabilities, [1, 4], [0, 3, 7])
        self.assertAlmostEqual(result.selected.support_coverage_probability, 1.0)
        self.assertLessEqual(result.selected.expected_detection_time, result.local_only.expected_detection_time)

    def test_incomplete_orbit_is_marked_infeasible(self):
        result = evaluate_periodic_policy(
            np.ones(12), local_steps=1, relocation_jump=3, max_cycles=24
        )
        self.assertFalse(result.feasible)
        self.assertLess(result.support_coverage_probability, 1.0)
        self.assertEqual(result.expected_detection_time, float("inf"))

    def test_zero_jump_matches_sequential_local_scan(self):
        result = evaluate_periodic_policy(np.ones(10), local_steps=2, relocation_jump=0)
        self.assertTrue(result.feasible)
        self.assertAlmostEqual(result.expected_detection_time, 5.5)
        self.assertEqual(result.relocation_count_to_worst, 0)


if __name__ == "__main__":
    unittest.main()
