import json

import numpy as np

from dsbc import compress_beliefs


rng = np.random.default_rng(39)
utilities = np.array([
    [5, 0, 0], [4, 0, 0], [3, 0, 0],
    [0, 5, 0], [0, 4, 0],
    [0, 0, 5], [0, 0, 4], [0, 0, 3],
])
beliefs = []
groups = ([0, 1, 2], [3, 4], [5, 6, 7])
for group in groups:
    for _ in range(40):
        concentration = np.full(8, .002)
        concentration[list(group)] = rng.uniform(.5, 3.0, size=len(group))
        beliefs.append(rng.dirichlet(concentration))

result = compress_beliefs(beliefs, utilities, maximum_regret=0)
print(json.dumps({
    "beliefs": result.original_belief_count,
    "hidden_states": len(utilities),
    "compressed_decision_states": result.compressed_state_count,
    "compression_fraction": result.compression_fraction,
    "maximum_decision_regret": result.global_maximum_regret,
    "actions": [cluster.prescribed_action for cluster in result.clusters],
    "members_per_cluster": [len(cluster.member_indices) for cluster in result.clusters],
    "certificate": result.merge_certificate,
    "status": result.status,
}, indent=2))
