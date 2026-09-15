"""Demonstrate nominal-versus-deployable stock and current bottleneck location."""

from __future__ import annotations

import json

from cdbl import ConnectedDeployableNetwork, StockNode, TransportEdge


def build_network() -> ConnectedDeployableNetwork:
    nodes = [
        StockNode("mine", 500.0, 0.90),
        StockNode("warehouse_a", 300.0, 0.80),
        StockNode("warehouse_b", 700.0, 0.20),
        StockNode("hub", 0.0),
        StockNode("processor", 0.0),
        StockNode("site", 0.0),
    ]
    edges = [
        TransportEdge("mine_to_hub", "mine", "hub", 250.0, 2, 0.95),
        TransportEdge("a_to_hub", "warehouse_a", "hub", 200.0, 1, 0.98),
        TransportEdge("b_to_hub_late", "warehouse_b", "hub", 400.0, 5, 0.90),
        TransportEdge("b_to_processor", "warehouse_b", "processor", 80.0, 2, 0.90),
        TransportEdge("hub_to_processor", "hub", "processor", 300.0, 2, 0.95),
        TransportEdge("processor_to_site", "processor", "site", 180.0, 1, 0.98),
    ]
    return ConnectedDeployableNetwork(nodes, edges, "site", horizon=5)


def main() -> None:
    network = build_network()
    result = network.solve()
    impacts = network.rank_bottlenecks(added_capacity=20.0)
    print(
        json.dumps(
            {
                "nominal_stock": result.nominal_stock,
                "active_stock": result.active_stock,
                "deployable_to_deadline": result.deployable_to_target,
                "nominal_to_deployable_ratio": result.connectivity_conversion_ratio,
                "edge_flows": result.edge_flows,
                "top_bottlenecks": [impact.__dict__ for impact in impacts[:6]],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

