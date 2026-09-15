import json
import numpy as np

from slerm import monitor_lock_in


sample_rate = 100.0
time = np.arange(0, 80, 1 / sample_rate)
forcing = np.sin(2 * np.pi * 1.5 * time)
displacement = np.empty_like(time)
early = time < 40
displacement[early] = 0.12 * np.sin(2 * np.pi * 1.0 * time[early])
displacement[~early] = -1.3 * np.cos(2 * np.pi * 1.5 * time[~early])

result = monitor_lock_in(
    forcing, displacement, sample_rate=sample_rate,
    window_samples=2000, step_samples=1000,
    dangerous_response_rms=.5,
)
print(json.dumps(result.to_dict(), indent=2))
