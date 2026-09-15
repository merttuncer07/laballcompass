import unittest

import numpy as np

from pitrat_preisach import (
    DensePreisach,
    FrontierPreisach,
    complete_multipartite_graph,
    masked_low_rank_weights,
    solve_coloring,
)


class PitratPreisachTests(unittest.TestCase):
    def test_coloring_solver_preserves_satisfiability(self):
        graph = complete_multipartite_graph(3, 3)
        self.assertTrue(solve_coloring(graph, 3, {}, "none").solved)
        self.assertFalse(solve_coloring(graph, 3, {0: 0, 1: 1}, "core").solved)

    def test_frontier_matches_dense_relays(self):
        rng = np.random.default_rng(4)
        left = rng.normal(size=(20, 3))
        right = rng.normal(size=(20, 3))
        dense = DensePreisach(masked_low_rank_weights(left, right))
        frontier = FrontierPreisach(left, right)
        for level in (2, 9, 4, 15, 1, 19, 7):
            self.assertAlmostEqual(dense.update(level), frontier.update(level), places=9)
            np.testing.assert_array_equal(dense.state, frontier.expanded_state())


if __name__ == "__main__":
    unittest.main()
