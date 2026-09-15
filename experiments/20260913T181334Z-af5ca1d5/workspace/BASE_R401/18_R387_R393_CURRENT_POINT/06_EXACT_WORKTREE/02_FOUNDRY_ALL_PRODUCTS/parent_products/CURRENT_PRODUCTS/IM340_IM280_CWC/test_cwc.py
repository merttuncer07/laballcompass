import unittest

import numpy as np

from cwc import CalibrationWidthController, interval_score


class CWCTests(unittest.TestCase):
    def test_repeated_misses_increase_width(self):
        controller = CalibrationWidthController(initial_multiplier=1.0)
        before = controller.multiplier
        for _ in range(20):
            controller.observe(5.0, 0.0, 1.0)
        self.assertGreater(controller.multiplier, before)

    def test_repeated_easy_hits_reduce_width(self):
        controller = CalibrationWidthController(initial_multiplier=3.0)
        before = controller.multiplier
        for _ in range(100):
            controller.observe(0.0, 0.0, 1.0)
        self.assertLess(controller.multiplier, before)

    def test_interval_score_penalizes_miss_distance(self):
        inside = interval_score(0.0, -1.0, 1.0, 0.1)
        near_miss = interval_score(1.1, -1.0, 1.0, 0.1)
        far_miss = interval_score(2.0, -1.0, 1.0, 0.1)
        self.assertLess(inside, near_miss)
        self.assertLess(near_miss, far_miss)


if __name__ == "__main__":
    unittest.main()

