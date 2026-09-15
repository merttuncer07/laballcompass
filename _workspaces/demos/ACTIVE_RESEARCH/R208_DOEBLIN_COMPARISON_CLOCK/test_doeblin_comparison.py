import unittest

import numpy as np

from doeblin_comparison import (
    drift_x,
    simulate_raw_euler,
    simulate_transformed_euler,
    transform_to_x,
    transform_to_y,
)


class DoeblinComparisonTests(unittest.TestCase):
    def test_coordinate_map_is_invertible(self):
        values = np.linspace(-4.0, 4.0, 101)
        self.assertTrue(np.allclose(transform_to_x(transform_to_y(values)), values))

    def test_calendar_time_drifts_are_pointwise_ordered(self):
        grid = np.linspace(-5.0, 5.0, 501)[:, None]
        values = drift_x(grid, np.array([-0.55, 0.0, 0.55]))
        self.assertTrue(np.all(values[:, 0] <= values[:, 1]))
        self.assertTrue(np.all(values[:, 1] <= values[:, 2]))

    def test_transformed_euler_preserves_pathwise_order(self):
        result = simulate_transformed_euler(paths=20_000, steps=20, seed=4)
        self.assertEqual(result["order_failure_rate"], 0.0)
        self.assertEqual(result["nonfinite_rate"], 0.0)

    def test_raw_euler_exposes_order_failure(self):
        result = simulate_raw_euler(paths=20_000, steps=20, seed=4)
        self.assertGreater(result["order_failure_rate"], 0.01)


if __name__ == "__main__":
    unittest.main()

