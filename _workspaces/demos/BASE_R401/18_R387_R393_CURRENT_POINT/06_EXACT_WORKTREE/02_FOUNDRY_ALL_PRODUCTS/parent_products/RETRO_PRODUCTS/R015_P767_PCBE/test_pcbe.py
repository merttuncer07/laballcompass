import unittest

import numpy as np

from pcbe import estimate_channel_breakthrough


class Tests(unittest.TestCase):
    def test_spanning_channel_creates_breakthrough(self):
        baseline = np.ones((8, 12)); current = baseline.copy(); current[3, :] = 50
        result = estimate_channel_breakthrough(current, channel_threshold=20, baseline_conductance_field=baseline, minimum_system_jump_ratio=2)
        self.assertTrue(result.spanning)
        self.assertGreater(result.conductance_jump_ratio, 2)
        self.assertEqual(result.status, "SPANNING_CHANNEL_BREAKTHROUGH_DETECTED")

    def test_gap_prevents_spanning_claim(self):
        field = np.ones((8, 12)); field[3, :] = 50; field[3, 6] = 1
        result = estimate_channel_breakthrough(field, channel_threshold=20)
        self.assertFalse(result.spanning)
        self.assertEqual(result.status, "PREFERENTIAL_CHANNEL_NOT_YET_SPANNING")

    def test_spanning_path_without_large_jump_is_separate(self):
        baseline = np.ones((8, 12)); current = baseline.copy(); current[3, :] = 2
        result = estimate_channel_breakthrough(current, channel_threshold=1.5, baseline_conductance_field=baseline, minimum_system_jump_ratio=10)
        self.assertTrue(result.spanning)
        self.assertEqual(result.status, "CHANNEL_SPANS_WITHOUT_REQUIRED_SYSTEM_JUMP")

    def test_baseline_shape_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            estimate_channel_breakthrough(np.ones((3, 3)), channel_threshold=1, baseline_conductance_field=np.ones((2, 2)))


if __name__ == "__main__":
    unittest.main()
