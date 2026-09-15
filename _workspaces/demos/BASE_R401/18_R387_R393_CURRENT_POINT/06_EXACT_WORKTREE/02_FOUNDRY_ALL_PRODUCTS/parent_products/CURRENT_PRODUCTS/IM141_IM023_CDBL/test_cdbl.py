import unittest

from cdbl import ConnectedDeployableNetwork, StockNode, TransportEdge
from demo_deployable_network import build_network


class CDBLTests(unittest.TestCase):
    def test_chain_bottleneck_limits_delivery(self):
        network = ConnectedDeployableNetwork(
            [StockNode("s", 100.0), StockNode("m", 0.0), StockNode("t", 0.0)],
            [TransportEdge("wide", "s", "m", 80.0, 1), TransportEdge("narrow", "m", "t", 30.0, 1)],
            "t",
            2,
        )
        self.assertAlmostEqual(network.solve().deployable_to_target, 30.0)
        self.assertEqual(network.rank_bottlenecks(10.0)[0].name, "narrow")

    def test_disconnected_stock_does_not_increase_delivery(self):
        base = build_network().solve()
        self.assertLess(base.deployable_to_target, base.active_stock)
        self.assertLess(base.connectivity_conversion_ratio, 1.0)

    def test_deadline_blocks_too_slow_path(self):
        network = ConnectedDeployableNetwork(
            [StockNode("s", 100.0), StockNode("t", 0.0)],
            [TransportEdge("late", "s", "t", 100.0, 4)],
            "t",
            3,
        )
        self.assertAlmostEqual(network.solve().deployable_to_target, 0.0)


if __name__ == "__main__":
    unittest.main()

