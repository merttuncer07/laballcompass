import json

import numpy as np

from srcd import design_reporting_contract


def main() -> None:
    outcomes = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 45], dtype=float)
    contracts = {
        "mean": design_reporting_contract(outcomes, "MEAN", base_payment=1000).to_dict(),
        "median": design_reporting_contract(outcomes, "QUANTILE", level=0.5, base_payment=1000).to_dict(),
        "upper_quantile": design_reporting_contract(outcomes, "QUANTILE", level=0.9, base_payment=1000).to_dict(),
        "upper_expectile": design_reporting_contract(outcomes, "EXPECTILE", level=0.9, base_payment=1000).to_dict(),
        "broken_by_floor": design_reporting_contract(
            outcomes, "MEAN", base_payment=0, payment_floor=0
        ).to_dict(),
    }
    binary = [1, 0, 1, 1, 0, 1, 0, 1, 1, 1]
    contracts["event_probability"] = design_reporting_contract(binary, "BINARY_PROBABILITY", base_payment=1).to_dict()
    print(json.dumps(contracts, indent=2))


if __name__ == "__main__":
    main()
