import json

import numpy as np

from bicc import audit_concentration


def main() -> None:
    rng = np.random.default_rng(349)
    n, d = 80_000, 30
    base = rng.uniform(0.0, 1.0, size=(n, d))
    replacement = rng.uniform(0.0, 1.0, size=(n, d))

    distributed_weights = np.full(d, 1.0 / d)
    concentrated_weights = np.full(d, 0.25 / (d - 1))
    concentrated_weights[0] = 0.75

    distributed = audit_concentration(
        lambda row: float(distributed_weights @ row),
        base,
        replacement,
        global_coordinate_bounds=np.abs(distributed_weights),
        delta=0.05,
    )
    concentrated = audit_concentration(
        lambda row: float(concentrated_weights @ row),
        base,
        replacement,
        global_coordinate_bounds=np.abs(concentrated_weights),
        delta=0.05,
    )

    result = {
        "distributed_influence": distributed.to_dict(),
        "concentrated_influence": concentrated.to_dict(),
        "comparison": {
            "radius_ratio_concentrated_over_distributed": (
                concentrated.mcdiarmid_two_sided_radius / distributed.mcdiarmid_two_sided_radius
            ),
            "variance_ratio_concentrated_over_distributed": (
                concentrated.empirical_output_variance / distributed.empirical_output_variance
            ),
            "interpretation": "Same input range and same total weight; concentration worsens when one input dominates.",
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
