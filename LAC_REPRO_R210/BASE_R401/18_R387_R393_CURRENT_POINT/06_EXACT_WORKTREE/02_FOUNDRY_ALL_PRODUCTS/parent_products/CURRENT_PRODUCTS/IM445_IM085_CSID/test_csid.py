from __future__ import annotations

import unittest

from csid import ContractSafeguardDesigner, FailureMode, Safeguard, designer_from_config


class ContractSafeguardDesignerTests(unittest.TestCase):
    def test_same_evidence_family_is_not_multiplied(self) -> None:
        designer = ContractSafeguardDesigner(
            [FailureMode("failure", 1.0, 100.0)],
            [
                Safeguard("a", 0.0, "same", {"failure": 0.5}),
                Safeguard("b", 0.0, "same", {"failure": 0.6}),
            ],
        )
        result = designer.evaluate(designer.safeguards, family_aware=True)
        self.assertAlmostEqual(result.coverage_by_failure["failure"], 0.6)

    def test_distinct_evidence_families_compose(self) -> None:
        designer = ContractSafeguardDesigner(
            [FailureMode("failure", 1.0, 100.0)],
            [
                Safeguard("a", 0.0, "one", {"failure": 0.5}),
                Safeguard("b", 0.0, "two", {"failure": 0.6}),
            ],
        )
        result = designer.evaluate(designer.safeguards, family_aware=True)
        self.assertAlmostEqual(result.coverage_by_failure["failure"], 0.8)

    def test_budget_is_respected(self) -> None:
        designer = ContractSafeguardDesigner(
            [FailureMode("failure", 0.5, 100.0)],
            [
                Safeguard("cheap", 2.0, "one", {"failure": 0.5}),
                Safeguard("expensive", 8.0, "two", {"failure": 0.9}),
            ],
        )
        result = designer.design(3.0)
        self.assertLessEqual(result["selected"]["total_cost"], 3.0)
        self.assertNotIn("expensive", result["selected"]["safeguards"])

    def test_config_interface(self) -> None:
        designer = designer_from_config(
            {
                "failure_modes": [{"name": "f", "probability": 0.1, "consequence": 10}],
                "safeguards": [
                    {"name": "s", "cost": 0, "evidence_family": "e", "coverage": {"f": 1}}
                ],
            }
        )
        self.assertEqual(designer.design(0)["selected"]["safeguards"], ("s",))


if __name__ == "__main__":
    unittest.main()
