import json
import numpy as np

from ispo import optimize_search_policy


probabilities = np.zeros(120)
probabilities[0:5] = 0.10
probabilities[60:65] = 0.10

result = optimize_search_policy(
    probabilities,
    local_step_candidates=[1, 2, 5, 10],
    relocation_jump_candidates=[0, 16, 35, 55, 59],
    relocation_speed=40.0,
    relocation_overhead=0.25,
)
print(json.dumps(result.to_dict(), indent=2))
