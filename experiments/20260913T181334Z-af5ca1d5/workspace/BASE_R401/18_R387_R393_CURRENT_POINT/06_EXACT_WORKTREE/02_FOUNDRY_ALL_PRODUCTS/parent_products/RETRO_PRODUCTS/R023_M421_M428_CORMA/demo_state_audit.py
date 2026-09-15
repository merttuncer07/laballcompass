import json

import numpy as np

from corma import audit_state_space


def main() -> None:
    # State 0 is controllable+observable; 1 observable only; 2 controllable only; 3 neither.
    a = np.diag([0.8, 0.6, 0.5, 0.3])
    b = np.array([[1.0], [0.0], [1.0], [0.0]])
    c = np.array([[1.0, 1.0, 0.0, 0.0]])
    audit = audit_state_space(a, b, c, horizon=12)

    full_impulse = [float((c @ np.linalg.matrix_power(a, k) @ b)[0, 0]) for k in range(10)]
    reduced_impulse = [0.8**k for k in range(10)]
    print(json.dumps({
        "audit": audit.to_dict(),
        "known_one_state_reduction_check": {
            "full_impulse": full_impulse,
            "reduced_impulse": reduced_impulse,
            "maximum_difference": max(abs(x - y) for x, y in zip(full_impulse, reduced_impulse)),
        },
    }, indent=2))


if __name__ == "__main__":
    main()
