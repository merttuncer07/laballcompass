import json
import numpy as np

from sacps import estimate_support_aware_covariance


rng = np.random.default_rng(21)
p = 12
factor_loadings = np.r_[np.full(6, 0.8), np.zeros(6)]
train = rng.normal(size=(28, p)) * 0.5 + rng.normal(size=(28, 1)) * factor_loadings
holdout = rng.normal(size=(600, p)) * 0.5 + rng.normal(size=(600, 1)) * factor_loadings
mask = np.eye(p, dtype=bool)
mask[:6, :6] = True

result = estimate_support_aware_covariance(
    train, mask, holdout_returns=holdout,
    shrinkage_grid=np.linspace(0, 1, 41), maximum_condition_number=1e5,
)
print(json.dumps(result.to_dict(), indent=2))
