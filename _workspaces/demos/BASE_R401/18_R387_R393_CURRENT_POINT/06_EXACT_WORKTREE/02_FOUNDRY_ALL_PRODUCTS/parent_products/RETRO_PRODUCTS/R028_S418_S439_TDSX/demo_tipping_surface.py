import json

import numpy as np

from tdsx import confounding_e_value, explore_sensitivity_surface, missing_mean_tipping_value


def main() -> None:
    surface = explore_sensitivity_surface(
        lambda p: 12.0 - 5.0 * p["hidden_confounding"] - 8.0 * p["missing_outcome_penalty"]
        + 2.0 * p["hidden_confounding"] * p["missing_outcome_penalty"],
        {
            "hidden_confounding": np.linspace(0, 2, 81),
            "missing_outcome_penalty": np.linspace(0, 1, 81),
        },
        {"hidden_confounding": 0.0, "missing_outcome_penalty": 0.0},
        decision_threshold=0.0,
    )
    print(json.dumps({
        "surface": surface.to_dict(),
        "risk_ratio_2_e_value": confounding_e_value(2.0),
        "missing_value_needed_to_tip_mean": missing_mean_tipping_value([8, 10, 12, 14], 2, 9.0),
    }, indent=2))


if __name__ == "__main__":
    main()
