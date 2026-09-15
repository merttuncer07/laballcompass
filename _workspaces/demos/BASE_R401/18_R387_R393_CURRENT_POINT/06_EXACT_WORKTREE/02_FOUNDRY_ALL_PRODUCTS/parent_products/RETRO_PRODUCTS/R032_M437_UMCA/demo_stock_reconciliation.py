"""Reconcile inventory change into movement, destruction, and creation."""

from __future__ import annotations

import json

import numpy as np

from umca import normalized_balanced_baseline, solve_unbalanced_transport


def main() -> None:
    source = np.array([80.0, 20.0])
    target = np.array([30.0, 100.0])
    movement = np.array([[1.0, 6.0], [5.0, 1.0]])
    result = solve_unbalanced_transport(
        source,
        target,
        movement,
        destruction_cost=np.array([1.2, 1.2]),
        creation_cost=np.array([1.8, 1.8]),
    )
    baseline = normalized_balanced_baseline(source, target, movement)
    output = {
        "source_total": float(source.sum()),
        "target_total": float(target.sum()),
        "unbalanced_accounting": {
            "flow": result.flow.tolist(),
            "destroyed_at_source": result.destroyed_at_source.tolist(),
            "created_at_target": result.created_at_target.tolist(),
            "moved_mass": result.moved_mass,
            "destroyed_mass": result.destroyed_mass,
            "created_mass": result.created_mass,
            "movement_cost": result.movement_cost,
            "destruction_cost": result.destruction_cost,
            "creation_cost": result.creation_cost,
            "total_cost": result.total_cost,
        },
        "normalized_balanced_baseline": {
            key: value.tolist() if isinstance(value, np.ndarray) else value for key, value in baseline.items()
        },
        "mass_falsely_recast_as_source_by_normalization": float(source.sum() * (baseline["source_rescaling_factor"] - 1.0)),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

