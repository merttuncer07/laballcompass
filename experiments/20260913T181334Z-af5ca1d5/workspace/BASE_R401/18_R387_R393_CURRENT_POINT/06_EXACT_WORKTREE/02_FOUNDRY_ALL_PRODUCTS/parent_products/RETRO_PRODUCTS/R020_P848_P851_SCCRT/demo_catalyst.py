import json
import numpy as np

from sccrt import design_regeneration_capacity


steps_per_half = 100
cycles = 8
reactant = np.tile(np.r_[np.ones(steps_per_half), np.zeros(steps_per_half)], cycles)
oxidant = np.tile(np.r_[np.zeros(steps_per_half), np.ones(steps_per_half)], cycles)
result = design_regeneration_capacity(
    reactant, oxidant, [.25, .5, 1, 2, 4],
    required_minimum_active_fraction=.25,
    required_final_active_fraction=.90,
    time_step=.02,
    reaction_rate_constant=.35,
    regeneration_rate_constant=.30,
    catalyst_lattice_capacity=100,
)
summary = result.to_dict(); summary.pop("candidates"); summary["selected"].pop("times"); summary["selected"].pop("active_lattice_fraction"); summary["selected"].pop("product_per_step"); summary["selected"].pop("regeneration_per_step")
print(json.dumps(summary, indent=2))
