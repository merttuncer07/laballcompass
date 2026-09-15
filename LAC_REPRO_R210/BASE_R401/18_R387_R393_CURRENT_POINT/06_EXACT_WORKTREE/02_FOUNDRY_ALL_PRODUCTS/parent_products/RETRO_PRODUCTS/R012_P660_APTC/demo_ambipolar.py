import json
import numpy as np

from aptc import calculate_ambipolar_transport


x = np.linspace(-5, 5, 401)
packet = .01 + np.exp(-x * x / (2 * .8 ** 2))
result = calculate_ambipolar_transport(
    x, packet, packet,
    electron_mobility=1400,
    hole_mobility=450,
    electron_diffusivity=35,
    hole_diffusivity=12,
    forecast_time=.05,
)
summary = result.to_dict()
for key in ("internal_electric_field", "electron_flux", "hole_flux"):
    summary.pop(key)
print(json.dumps(summary, indent=2))
