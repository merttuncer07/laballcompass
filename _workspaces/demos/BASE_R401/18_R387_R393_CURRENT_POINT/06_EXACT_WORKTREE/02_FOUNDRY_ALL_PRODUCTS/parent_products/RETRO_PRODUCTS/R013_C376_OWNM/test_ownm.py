import unittest

import numpy as np

from ownm import OwnershipWedgeNetworkMapper


class OWNMTests(unittest.TestCase):
    def test_pyramid_propagates_control_beyond_cash_majority(self):
        cash = np.array([[0.0, 0.51, 0.0], [0.0, 0.0, 0.51], [0.0, 0.0, 0.0]])
        mapper = OwnershipWedgeNetworkMapper(["A", "B", "C"], cash, cash)
        result = mapper.analyze(np.array([0.51, 0.0, 0.0]), np.array([0.51, 0.0, 0.0]))
        self.assertTrue(np.all(result.controlled))
        self.assertAlmostEqual(result.ultimate_cash_exposure[2], 0.51**3)
        self.assertGreater(result.control_to_cash_wedge[2], 7.0)

    def test_dual_class_control_uses_votes_not_cash(self):
        mapper = OwnershipWedgeNetworkMapper(["D"], np.zeros((1, 1)), np.zeros((1, 1)))
        result = mapper.analyze(np.array([0.10]), np.array([0.60]))
        self.assertTrue(result.controlled[0])
        self.assertAlmostEqual(result.control_to_cash_wedge[0], 10.0)

    def test_below_threshold_does_not_control(self):
        mapper = OwnershipWedgeNetworkMapper(["D"], np.zeros((1, 1)), np.zeros((1, 1)))
        result = mapper.analyze(np.array([0.40]), np.array([0.40]))
        self.assertFalse(result.controlled[0])

    def test_cross_ownership_cycle_is_reported(self):
        cash = np.array([[0.0, 0.1], [0.1, 0.0]])
        mapper = OwnershipWedgeNetworkMapper(["A", "B"], cash, cash)
        result = mapper.analyze(np.zeros(2), np.zeros(2))
        self.assertEqual(result.cross_ownership_components, (("A", "B"),))


if __name__ == "__main__":
    unittest.main()

