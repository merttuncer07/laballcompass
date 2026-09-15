import json
import numpy as np

from utdim import monitor_double_diffusive_instability


result = monitor_double_diffusive_instability(
    viscosity=.1,
    diffusivities=[1.0, .01],
    buoyancy_coefficients=[1.0, 1.0],
    background_gradients=[2.0, -1.0],
    wavenumbers=np.logspace(-1.5, 1.2, 160),
)
print(json.dumps(result.to_dict(), indent=2))
