import json
import numpy as np

from oasrd import select_operator_averaging


target = np.array([3.0, -2.0])
operator = lambda x: 2.0 * target - x
result = select_operator_averaging(
    operator, [20.0, 10.0], [1.0, .8, .5, .25, .1],
    maximum_iterations=100, residual_tolerance=1e-10,
)
summary = result.to_dict()
for run in summary["runs"]:
    run.pop("state_history"); run.pop("residual_history")
summary["selected"].pop("state_history"); summary["selected"].pop("residual_history")
if summary["direct_iteration"] is not None:
    summary["direct_iteration"].pop("state_history"); summary["direct_iteration"].pop("residual_history")
print(json.dumps(summary, indent=2))
