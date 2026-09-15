import json
import numpy as np

from rspi import identify_remote_synchronization


rng = np.random.default_rng(6)
time = np.linspace(0, 100, 4000)
phase_a = 1.3 * time + rng.normal(scale=.08, size=time.size)
phase_c = 1.3 * time + .45 + rng.normal(scale=.08, size=time.size)
phase_b = np.cumsum(rng.normal(scale=.35, size=time.size))
phases = np.column_stack([phase_a, phase_b, phase_c])
adjacency = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
result = identify_remote_synchronization(phases, adjacency, node_names=["A", "B", "C"])
print(json.dumps(result.to_dict(), indent=2))
