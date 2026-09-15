"""Attribute observed network flow to demand, local cycles, and global circulation."""

from __future__ import annotations

import json

import numpy as np

from hfad import HodgeFlowAttributionDecomposer, incidence_from_edges


def build_complex():
    # Filled triangle 0-1-2, bridge 2-3, and an unfilled square 3-4-5-6.
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)]
    boundary_1 = incidence_from_edges(7, edges)
    boundary_2 = np.zeros((len(edges), 1))
    boundary_2[0:3, 0] = 1.0
    return boundary_1, boundary_2


def main() -> None:
    boundary_1, boundary_2 = build_complex()
    node_potential = np.array([1.2, -0.4, 0.7, -0.2, 0.1, -0.3, 0.5])
    demand_flow = boundary_1.T @ node_potential
    local_recirculation = boundary_2[:, 0] * 2.0
    global_loop = np.zeros(8)
    global_loop[4:8] = 3.0
    observed = demand_flow + local_recirculation + global_loop
    result = HodgeFlowAttributionDecomposer(boundary_1, boundary_2).decompose(observed)
    unexplained_by_node_balance = observed - result.potential_flow
    output = {
        "observed_edge_flow": observed.tolist(),
        "potential_source_sink_flow": result.potential_flow.tolist(),
        "local_face_cycle_flow": result.local_cycle_flow.tolist(),
        "global_harmonic_loop_flow": result.harmonic_flow.tolist(),
        "energy_share": {
            "potential": result.potential_energy / float(observed @ observed),
            "local_cycle": result.local_cycle_energy / float(observed @ observed),
            "harmonic": result.harmonic_energy / float(observed @ observed),
        },
        "node_balance_only_unexplained_energy": float(unexplained_by_node_balance @ unexplained_by_node_balance),
        "reconstruction_residual": result.reconstruction_residual,
        "cycle_divergence_residual": result.divergence_residual_for_cycles,
        "nonlocal_face_curl_residual": result.face_curl_residual_for_potential_harmonic,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

