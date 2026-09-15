"""Reproducible CCVC demonstration on three conserved resource stocks."""

from __future__ import annotations

import json

import numpy as np

from ccvc import ConservationConstrainedViability


def build_system() -> ConservationConstrainedViability:
    drift = np.array(
        [
            [-0.08, 0.02, 0.01],
            [0.05, -0.06, 0.02],
            [0.03, 0.04, -0.03],
        ]
    )
    controls = np.array([[-1.0, 0.0, 1.0], [1.0, -1.0, 0.0], [0.0, 1.0, -1.0]])
    safe_matrix = np.vstack([np.eye(3), -np.eye(3)])
    safe_bound = np.concatenate([np.full(3, 0.80), np.full(3, -0.05)])
    return ConservationConstrainedViability(
        drift,
        controls,
        np.ones((1, 3)),
        np.array([1.0]),
        safe_matrix,
        safe_bound,
        np.full(3, -0.12),
        np.full(3, 0.12),
    )


def run(filtered: bool) -> dict[str, float | list[float]]:
    system = build_system()
    state = np.array([0.33, 0.33, 0.34])
    unsafe_target = np.array([0.92, 0.04, 0.04])
    step = 0.05
    maximum_violation = 0.0
    maximum_conservation_error = 0.0
    interventions = 0
    for _ in range(500):
        desired_velocity = 1.2 * (unsafe_target - state)
        nominal = np.linalg.lstsq(system.B, desired_velocity - system.drift(state), rcond=None)[0]
        nominal = np.clip(nominal, system.u_lower, system.u_upper)
        control = system.filter_control(state, nominal, step) if filtered else nominal
        interventions += int(np.linalg.norm(control - nominal) > 1e-7)
        state = state + step * system.velocity(state, control)
        maximum_violation = max(maximum_violation, float(np.max(system.A @ state - system.b)))
        maximum_conservation_error = max(
            maximum_conservation_error, float(np.max(np.abs(system.C @ state - system.c)))
        )
    return {
        "final_state": state.tolist(),
        "maximum_safe_set_violation": maximum_violation,
        "maximum_conservation_error": maximum_conservation_error,
        "filter_interventions": interventions,
    }


def main() -> None:
    system = build_system()
    certificate = system.certify_vertices()
    result = {
        "vertex_certificate": {
            "viable": certificate["viable"],
            "vertex_count": certificate["vertex_count"],
            "minimum_inward_margin": certificate["minimum_inward_margin"],
            "maximum_conservation_residual": certificate["maximum_conservation_residual"],
        },
        "unfiltered_nominal_control": run(False),
        "ccvc_filtered_control": run(True),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

