import json
import numpy as np

from vico import optimize_coupling


x = np.arange(0.0, 11.0)
activation = np.vstack([x + 1.0, x + 2.0, x + 0.5])
release = np.vstack([13.0 - x, 11.0 - x, 11.5 - x])

expected = optimize_coupling(x, activation, release)
robust = optimize_coupling(x, activation, release, selection_mode="MINIMAX_REGRET")

too_narrow_x = np.arange(0.0, 4.0)
too_narrow = optimize_coupling(
    too_narrow_x, too_narrow_x + 1.0, 11.0 - too_narrow_x
)

print(json.dumps({
    "expected": expected.to_dict(),
    "robust": robust.to_dict(),
    "too_narrow": too_narrow.to_dict(),
}, indent=2))
