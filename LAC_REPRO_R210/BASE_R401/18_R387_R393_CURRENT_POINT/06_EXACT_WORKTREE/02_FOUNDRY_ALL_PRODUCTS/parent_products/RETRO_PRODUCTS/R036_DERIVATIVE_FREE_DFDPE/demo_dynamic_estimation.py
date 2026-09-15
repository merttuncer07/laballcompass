import json

import numpy as np

from dfdpe import estimate_affine_dynamics, simulate_affine_dynamics


rng = np.random.default_rng(14)
times = np.linspace(0, 40, 801)
inputs = .7 * np.sin(.63 * times) + .35 * np.sin(1.71 * times) + (times > 17) * .45
truth = np.array([-.42, 1.35, .22])
clean = simulate_affine_dynamics(times, inputs, 1.7, truth)
observed = clean + rng.normal(scale=.20, size=clean.size)

validation_times = np.linspace(0, 18, 361)
validation_inputs = .5 * np.cos(.47 * validation_times) - .4 * np.sin(1.23 * validation_times)
validation_outputs = simulate_affine_dynamics(validation_times, validation_inputs, -.8, truth)

result = estimate_affine_dynamics(
    times, observed, inputs,
    window_duration=4,
    window_step=.5,
    validation_times=validation_times,
    validation_outputs=validation_outputs,
    validation_inputs=validation_inputs,
)
summary = {
    "truth": truth.tolist(),
    "estimate": result.estimate.to_dict() if hasattr(result.estimate, "to_dict") else {
        "persistence": result.estimate.persistence,
        "input_gain": result.estimate.input_gain,
        "drift": result.estimate.drift,
        "validation_rollout_rmse": result.estimate.validation_rollout_rmse,
    },
    "finite_difference_baseline": {
        "persistence": result.finite_difference_baseline.persistence,
        "input_gain": result.finite_difference_baseline.input_gain,
        "drift": result.finite_difference_baseline.drift,
        "validation_rollout_rmse": result.finite_difference_baseline.validation_rollout_rmse,
    },
    "windows": result.number_of_windows,
    "design_rank": result.design_rank,
    "condition_number": result.design_condition_number,
    "status": result.status,
}
print(json.dumps(summary, indent=2))
