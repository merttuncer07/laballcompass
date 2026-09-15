import unittest

import numpy as np

from umca import solve_unbalanced_transport


class UMCATests(unittest.TestCase):
    def test_unequal_total_requires_net_creation(self):
        result = solve_unbalanced_transport(
            np.array([10.0]), np.array([13.0]), np.array([[1.0]]), 2.0, 2.0
        )
        self.assertAlmostEqual(result.created_mass - result.destroyed_mass, 3.0)

    def test_expensive_cross_move_uses_local_destroy_and_create(self):
        result = solve_unbalanced_transport(
            np.array([10.0, 0.0]),
            np.array([0.0, 10.0]),
            np.array([[0.0, 10.0], [10.0, 0.0]]),
            1.0,
            1.0,
        )
        self.assertAlmostEqual(result.moved_mass, 0.0)
        self.assertAlmostEqual(result.destroyed_mass, 10.0)
        self.assertAlmostEqual(result.created_mass, 10.0)

    def test_cheap_equal_mass_transport_moves_without_mass_change(self):
        result = solve_unbalanced_transport(
            np.array([7.0]), np.array([7.0]), np.array([[0.5]]), 2.0, 2.0
        )
        self.assertAlmostEqual(result.moved_mass, 7.0)
        self.assertAlmostEqual(result.destroyed_mass, 0.0)
        self.assertAlmostEqual(result.created_mass, 0.0)

    def test_accounting_balances_hold(self):
        result = solve_unbalanced_transport(
            np.array([8.0, 2.0]), np.array([3.0, 10.0]), np.array([[1.0, 6.0], [5.0, 1.0]]), 1.2, 1.8
        )
        self.assertLess(result.source_balance_residual, 1e-9)
        self.assertLess(result.target_balance_residual, 1e-9)


if __name__ == "__main__":
    unittest.main()

