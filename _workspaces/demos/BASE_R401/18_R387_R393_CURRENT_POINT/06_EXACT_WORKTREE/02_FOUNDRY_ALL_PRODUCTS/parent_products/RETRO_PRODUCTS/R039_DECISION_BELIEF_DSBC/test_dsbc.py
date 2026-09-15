import unittest

import numpy as np

from dsbc import compress_beliefs


UTILITIES = np.array([
    [4, 0, 0], [3, 0, 0],
    [0, 4, 0], [0, 3, 0],
    [0, 0, 4], [0, 0, 3],
])


class Tests(unittest.TestCase):
    def test_action_equivalent_beliefs_compress_without_regret(self):
        beliefs = np.array([
            [.7, .3, 0, 0, 0, 0], [.2, .8, 0, 0, 0, 0],
            [0, 0, .6, .4, 0, 0], [0, 0, .1, .9, 0, 0],
            [0, 0, 0, 0, .8, .2], [0, 0, 0, 0, .3, .7],
        ])
        result = compress_beliefs(beliefs, UTILITIES, maximum_regret=0)
        self.assertEqual(result.compressed_state_count, 3)
        self.assertAlmostEqual(result.global_maximum_regret, 0)
        self.assertEqual({cluster.prescribed_action for cluster in result.clusters}, {0, 1, 2})

    def test_same_most_likely_state_does_not_override_decision_loss(self):
        utilities = np.array([[1, 0], [0, 3], [0, 0]])
        beliefs = [[.60, .39, .01], [.60, .10, .30]]
        result = compress_beliefs(beliefs, utilities, maximum_regret=0)
        self.assertEqual(result.compressed_state_count, 2)

    def test_controlled_loss_allows_more_compression_and_reports_bound(self):
        utilities = np.array([[1, 0], [0, 1]])
        beliefs = [[.55, .45], [.45, .55], [.52, .48]]
        result = compress_beliefs(beliefs, utilities, maximum_regret=.11)
        self.assertEqual(result.compressed_state_count, 1)
        self.assertLessEqual(result.global_maximum_regret, .11 + 1e-12)

    def test_invalid_belief_is_rejected(self):
        with self.assertRaises(ValueError):
            compress_beliefs([[.8, .8]], [[1, 0], [0, 1]], maximum_regret=0)


if __name__ == "__main__":
    unittest.main()
