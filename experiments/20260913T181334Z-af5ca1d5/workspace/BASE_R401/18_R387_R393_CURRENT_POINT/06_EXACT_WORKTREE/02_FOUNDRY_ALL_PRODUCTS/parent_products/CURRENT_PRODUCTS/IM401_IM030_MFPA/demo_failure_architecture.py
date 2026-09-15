"""Compare a composed failure path with equal-mass single-route designs."""

from __future__ import annotations

import json

from mfpa import DissipationMechanism, MultiRouteFailurePathArchitect


def build_designer() -> MultiRouteFailurePathArchitect:
    mechanisms = [
        DissipationMechanism(
            "sacrificial_layer",
            0.70,
            8.0,
            0.35,
            {"nominal": 1.0, "wet": 0.35, "hot": 0.70, "misaligned": 1.0},
            "interface",
        ),
        DissipationMechanism(
            "crack_deflection",
            1.75,
            6.5,
            0.45,
            {"nominal": 1.0, "wet": 0.95, "hot": 1.0, "misaligned": 0.40},
            "geometry",
        ),
        DissipationMechanism(
            "fiber_pullout",
            2.50,
            7.5,
            0.40,
            {"nominal": 1.0, "wet": 0.75, "hot": 0.45, "misaligned": 0.55},
            "bridging",
        ),
        DissipationMechanism(
            "phase_transformation",
            3.25,
            9.0,
            0.25,
            {"nominal": 1.0, "wet": 1.0, "hot": 0.55, "misaligned": 0.90},
            "phase",
        ),
    ]
    return MultiRouteFailurePathArchitect(mechanisms, ["nominal", "wet", "hot", "misaligned"])


def serializable(result):
    return {
        "allocation": result.allocation,
        "scenario_failure_energy": result.scenario_failure_energy,
        "activated_routes": {key: list(value) for key, value in result.activated_routes.items()},
        "worst_case_energy": result.worst_case_energy,
        "mean_energy": result.mean_energy,
        "failure_family_concentration": result.failure_family_concentration,
    }


def main() -> None:
    designer = build_designer()
    composed = designer.optimize(total_mass=1.0, mass_step=0.05)
    single = designer.best_single_route(total_mass=1.0)
    print(
        json.dumps(
            {
                "equal_total_mass": 1.0,
                "optimized_composed": serializable(composed),
                "best_single_route": serializable(single),
                "worst_case_energy_gain": composed.worst_case_energy - single.worst_case_energy,
                "worst_case_relative_gain": composed.worst_case_energy / single.worst_case_energy - 1.0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

