import json
import numpy as np

from dhcc import calibrate_hedge_covariance


rng = np.random.default_rng(18)
n_train, n_validation = 22, 1200
z_train = rng.normal(size=n_train)
x_train = np.column_stack([
    z_train + rng.normal(scale=.03, size=n_train),
    z_train + rng.normal(scale=.03, size=n_train),
    rng.normal(size=n_train),
])
y_train = z_train + .25 * x_train[:, 2] + rng.normal(scale=.35, size=n_train)
z_val = rng.normal(size=n_validation)
x_val = np.column_stack([
    z_val + rng.normal(scale=.20, size=n_validation),
    z_val + rng.normal(scale=.20, size=n_validation),
    rng.normal(size=n_validation),
])
y_val = z_val + .25 * x_val[:, 2] + rng.normal(scale=.35, size=n_validation)

result = calibrate_hedge_covariance(
    y_train, x_train, y_val, x_val,
    ridge_grid=[0, .001, .003, .01, .03, .1, .3, 1.0],
)
print(json.dumps(result.to_dict(), indent=2))
