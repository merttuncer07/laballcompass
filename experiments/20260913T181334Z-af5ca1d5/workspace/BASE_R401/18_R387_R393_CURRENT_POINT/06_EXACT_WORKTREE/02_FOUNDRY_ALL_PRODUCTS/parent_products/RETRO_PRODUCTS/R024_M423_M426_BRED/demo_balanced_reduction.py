import json

import numpy as np

from bred import design_balanced_reduction


def main() -> None:
    a = np.diag([0.92, 0.75, 0.50, 0.30, 0.15, 0.05])
    b = np.array([[1.0], [0.50], [0.20], [0.05], [0.01], [0.002]])
    c = np.array([[1.0, 0.80, 0.30, 0.10, 0.02, 0.005]])
    result = design_balanced_reduction(a, b, c, error_budget=0.02, impulse_horizon=300)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
