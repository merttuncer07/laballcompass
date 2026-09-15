"""Demonstrate pyramid and dual-class control with small economic exposure."""

from __future__ import annotations

import json

import numpy as np

from ownm import OwnershipWedgeNetworkMapper


def main() -> None:
    names = ["HoldCo", "MidCo", "OperatingCo", "DualClassTech"]
    cash = np.zeros((4, 4))
    votes = np.zeros((4, 4))
    cash[0, 1] = votes[0, 1] = 0.51
    cash[1, 2] = votes[1, 2] = 0.51
    mapper = OwnershipWedgeNetworkMapper(names, cash, votes)
    result = mapper.analyze(
        investor_direct_cash=np.array([0.51, 0.0, 0.0, 0.10]),
        investor_direct_votes=np.array([0.51, 0.0, 0.0, 0.60]),
        company_asset_values=np.array([100.0, 300.0, 1000.0, 700.0]),
    )
    rows = []
    for index, name in enumerate(names):
        rows.append(
            {
                "company": name,
                "ultimate_cash_exposure": float(result.ultimate_cash_exposure[index]),
                "commanded_voting_power": float(result.commanded_voting_power[index]),
                "controlled": bool(result.controlled[index]),
                "control_round": int(result.control_round[index]),
                "control_to_cash_wedge": float(result.control_to_cash_wedge[index]),
            }
        )
    output = {
        "companies": rows,
        "controlled_asset_value": result.controlled_asset_value,
        "cash_at_risk_value": result.cash_at_risk_value,
        "controlled_asset_to_cash_at_risk": result.controlled_asset_to_cash_at_risk,
        "cash_majority_baseline_would_control": [
            name for name, exposure in zip(names, result.ultimate_cash_exposure) if exposure >= 0.5
        ],
        "cross_ownership_components": [list(component) for component in result.cross_ownership_components],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

