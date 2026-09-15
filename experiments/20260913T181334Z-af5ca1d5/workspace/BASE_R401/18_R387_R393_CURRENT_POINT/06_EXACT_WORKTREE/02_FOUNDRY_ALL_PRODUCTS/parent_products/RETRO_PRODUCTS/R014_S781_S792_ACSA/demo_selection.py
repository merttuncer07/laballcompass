import json
import numpy as np

from acsa import audit_adaptive_selection


rng = np.random.default_rng(42)
n = 240
selection = np.column_stack([
    rng.normal(0.30, 0.05, n),
    rng.normal(0.27, 0.05, n),
    rng.normal(0.18, 0.04, n),
])
holdout = np.column_stack([
    rng.normal(0.30, 0.05, n),
    rng.normal(0.27, 0.05, n),
    rng.normal(0.43, 0.05, n),
])

audit = audit_adaptive_selection(
    selection,
    holdout,
    candidate_names=["stable_baseline", "real_improvement", "adaptive_decoy"],
    bootstrap_samples=2000,
    random_seed=9,
    material_regret=0.01,
)
print(json.dumps(audit.to_dict(), indent=2))
