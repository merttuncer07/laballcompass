import unittest

import numpy as np

from rspi import identify_remote_synchronization


class Tests(unittest.TestCase):
    def test_remote_pair_is_found_through_unsynchronized_mediator(self):
        rng = np.random.default_rng(1); t = np.linspace(0, 50, 2000)
        a = t + rng.normal(scale=.05, size=t.size); c = t + .3 + rng.normal(scale=.05, size=t.size)
        b = np.cumsum(rng.normal(scale=.4, size=t.size))
        result = identify_remote_synchronization(np.column_stack([a, b, c]), [[0,1,0],[1,0,1],[0,1,0]], node_names=["A","B","C"])
        self.assertEqual(result.status, "REMOTE_SYNCHRONIZATION_PATHWAY_FOUND")
        self.assertEqual(result.remote_pairs[0].graph_path, ("A", "B", "C"))
        self.assertGreater(result.remote_pairs[0].endpoint_phase_locking, .9)

    def test_synchronized_mediator_prevents_remote_label(self):
        t = np.linspace(0, 50, 1000); phases = np.column_stack([t, t+.1, t+.2])
        result = identify_remote_synchronization(phases, [[0,1,0],[1,0,1],[0,1,0]])
        self.assertEqual(result.status, "NO_REMOTE_SYNCHRONIZATION_PATHWAY_FOUND")
        self.assertEqual(result.synchronized_nonadjacent_pair_count, 1)

    def test_adjacent_synchrony_is_not_remote(self):
        rng = np.random.default_rng(2); t=np.linspace(0,20,500)
        phases=np.column_stack([t,t+.1,np.cumsum(rng.normal(size=t.size))])
        result=identify_remote_synchronization(phases, [[0,1,0],[1,0,1],[0,1,0]])
        self.assertEqual(len(result.remote_pairs),0)

    def test_asymmetric_adjacency_is_rejected(self):
        with self.assertRaises(ValueError):
            identify_remote_synchronization(np.ones((20,3)), [[0,1,0],[0,0,1],[0,1,0]])


if __name__ == "__main__":
    unittest.main()
