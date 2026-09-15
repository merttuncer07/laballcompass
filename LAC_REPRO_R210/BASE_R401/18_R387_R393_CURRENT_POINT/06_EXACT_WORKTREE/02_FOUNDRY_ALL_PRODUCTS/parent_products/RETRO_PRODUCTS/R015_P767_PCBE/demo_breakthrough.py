import json
import numpy as np

from pcbe import estimate_channel_breakthrough


baseline = np.ones((20, 40))
current = baseline.copy()
current[9, :] = 100.0
result = estimate_channel_breakthrough(
    current,
    channel_threshold=50,
    baseline_conductance_field=baseline,
    minimum_system_jump_ratio=3,
)
summary = result.to_dict(); summary["widest_path"] = f"{len(result.widest_path)} cells"
print(json.dumps(summary, indent=2))
