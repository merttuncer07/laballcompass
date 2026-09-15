import json

import numpy as np

from sce import run_specification_curve


def main() -> None:
    rng = np.random.default_rng(440)
    n = 2_000
    demand_pressure = rng.normal(size=n)
    campaign = 0.8 * demand_pressure + rng.normal(size=n)
    revenue = 0.6 * campaign + 1.7 * demand_pressure + rng.normal(scale=0.9, size=n)
    revenue[0] += 20.0
    clipped_revenue = np.clip(revenue, *np.quantile(revenue, [0.01, 0.99]))

    curve = run_specification_curve(
        outcomes={"raw_revenue": revenue, "clipped_revenue": clipped_revenue},
        treatments={"campaign_intensity": campaign},
        controls={"demand_pressure": demand_pressure},
        control_sets={"unadjusted": [], "demand_adjusted": ["demand_pressure"]},
        samples={"all": np.ones(n, dtype=bool), "central_demand": np.abs(demand_pressure) < 1.5},
    )
    print(json.dumps(curve.to_dict(), indent=2))


if __name__ == "__main__":
    main()
