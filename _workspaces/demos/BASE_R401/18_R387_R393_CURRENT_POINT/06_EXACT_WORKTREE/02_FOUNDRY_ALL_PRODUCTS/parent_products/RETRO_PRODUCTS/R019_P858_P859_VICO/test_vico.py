import unittest

import numpy as np

from vico import optimize_coupling


class Tests(unittest.TestCase):
    def test_symmetric_two_bottleneck_problem_has_interior_optimum(self):
        x = np.arange(11.0)
        result = optimize_coupling(x, x + 1.0, 11.0 - x)
        self.assertEqual(result.selected_coupling, 5.0)
        self.assertTrue(result.interior_selected)
        self.assertEqual(result.status, "INTERIOR_COUPLING_OPTIMUM_FOUND")
        self.assertAlmostEqual(result.selected_aggregate_throughput, 3.0)

    def test_minimax_regret_handles_scenarios(self):
        x = np.arange(11.0)
        activation = np.vstack([x + 1.0, x + 2.0, x + 0.5])
        release = np.vstack([13.0 - x, 11.0 - x, 11.5 - x])
        result = optimize_coupling(x, activation, release, selection_mode="MINIMAX_REGRET")
        self.assertIn(result.selected_coupling, (4.0, 5.0, 6.0))
        self.assertGreaterEqual(result.selected_worst_case_regret, 0.0)

    def test_assumption_failure_returns_exact_witness(self):
        x = np.arange(5.0)
        result = optimize_coupling(x, [1, 3, 2, 4, 5], [6, 5, 4, 3, 2])
        self.assertFalse(result.activation_nondecreasing)
        self.assertEqual(result.activation_violation.low_coupling, 1.0)
        self.assertEqual(result.activation_violation.high_coupling, 2.0)
        self.assertEqual(result.activation_violation.violation, 1.0)

    def test_boundary_result_reports_insufficient_range(self):
        x = np.arange(4.0)
        result = optimize_coupling(x, x + 1.0, 11.0 - x)
        self.assertFalse(result.interior_selected)
        self.assertEqual(result.status, "SEARCH_RANGE_MISSES_INTERIOR_OPTIMUM")


if __name__ == "__main__":
    unittest.main()
