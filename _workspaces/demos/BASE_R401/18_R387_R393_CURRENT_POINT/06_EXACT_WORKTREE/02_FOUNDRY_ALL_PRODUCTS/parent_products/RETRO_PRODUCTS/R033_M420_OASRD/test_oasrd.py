import unittest

import numpy as np

from oasrd import run_averaged_operator, select_operator_averaging


class Tests(unittest.TestCase):
    def test_averaging_stabilizes_reflection_cycle(self):
        target = np.array([2., -1.]); operator = lambda x: 2 * target - x
        result = select_operator_averaging(operator, [10, 4], [1, .75, .5, .25], maximum_iterations=50)
        self.assertEqual(result.selected.alpha, .5)
        self.assertTrue(result.selected.converged)
        self.assertTrue(np.allclose(result.selected.final_state, target))
        self.assertFalse(result.direct_iteration.converged)

    def test_direct_contraction_can_remain_best(self):
        operator = lambda x: .5 * x + 1
        result = select_operator_averaging(operator, [10], [1, .5, .2], maximum_iterations=100)
        self.assertEqual(result.selected.alpha, 1)
        self.assertTrue(result.selected.converged)

    def test_nonconvergence_returns_best_residual_without_deleting_runs(self):
        operator = lambda x: x + 1
        result = select_operator_averaging(operator, [0], [1, .5, .1], maximum_iterations=5)
        self.assertEqual(result.status, "NO_CANDIDATE_CONVERGED_BEST_RESIDUAL_RETURNED")
        self.assertEqual(len(result.runs), 3)

    def test_invalid_operator_output_is_visible(self):
        run = run_averaged_operator(lambda x: [np.nan], [1], alpha=.5)
        self.assertEqual(run.status, "OPERATOR_RETURNED_INVALID_STATE")


if __name__ == "__main__":
    unittest.main()
