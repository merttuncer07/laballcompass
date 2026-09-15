import json
import numpy as np

from csdc import simulate_curvature_coarsening


rng = np.random.default_rng(12)
radii = rng.lognormal(mean=0.0, sigma=.28, size=500)
result = simulate_curvature_coarsening(
    radii,
    mobility=.035,
    maximum_time=40,
    time_step=.01,
    target_mean_radius=1.20,
    record_every_steps=100,
)
summary = result.to_dict()
summary.pop("initial_radii"); summary.pop("final_radii"); summary.pop("states")
print(json.dumps(summary, indent=2))
