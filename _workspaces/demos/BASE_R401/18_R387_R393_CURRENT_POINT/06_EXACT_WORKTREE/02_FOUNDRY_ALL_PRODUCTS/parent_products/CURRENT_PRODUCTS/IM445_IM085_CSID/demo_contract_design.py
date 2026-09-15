from __future__ import annotations

import json
from pathlib import Path

from csid import ContractSafeguardDesigner, FailureMode, Safeguard


def build_designer() -> ContractSafeguardDesigner:
    return ContractSafeguardDesigner(
        [
            FailureMode("hidden_effort", 0.18, 100.0),
            FailureMode("sales_report_manipulation", 0.12, 90.0),
            FailureMode("decision_right_relocation", 0.10, 120.0),
        ],
        [
            Safeguard(
                "sales_rebate_monitor",
                2.0,
                "sales_system",
                {"hidden_effort": 0.65, "sales_report_manipulation": 0.75},
            ),
            Safeguard(
                "revenue_share_audit",
                2.0,
                "sales_system",
                {"hidden_effort": 0.60, "sales_report_manipulation": 0.80},
            ),
            Safeguard(
                "customer_retention_signal",
                4.0,
                "customer_outcome",
                {"hidden_effort": 0.75, "sales_report_manipulation": 0.25},
            ),
            Safeguard(
                "physical_inventory_attestation",
                4.0,
                "physical_inventory",
                {"sales_report_manipulation": 0.70, "decision_right_relocation": 0.45},
            ),
            Safeguard(
                "decision_right_exception_review",
                3.0,
                "governance",
                {"hidden_effort": 0.20, "decision_right_relocation": 0.80},
            ),
        ],
    )


def evaluate() -> dict[str, object]:
    designer = build_designer()
    budget = 7.0
    naive_design = designer.design(budget, family_aware=False)
    family_design = designer.design(budget, family_aware=True)

    by_name = {safeguard.name: safeguard for safeguard in designer.safeguards}
    naive_selected = [by_name[name] for name in naive_design["selected"]["safeguards"]]
    naive_in_reality = designer.evaluate(naive_selected, family_aware=True)

    return {
        "budget": budget,
        "naive_independence_design": naive_design["selected"],
        "naive_design_under_common_evidence_reality": naive_in_reality.as_dict(),
        "family_aware_design": family_design["selected"],
        "family_aware_top_portfolios": family_design["top_portfolios"][:5],
        "real_objective_improvement": 1.0
        - family_design["selected"]["objective"] / naive_in_reality.objective,
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("contract_design_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
