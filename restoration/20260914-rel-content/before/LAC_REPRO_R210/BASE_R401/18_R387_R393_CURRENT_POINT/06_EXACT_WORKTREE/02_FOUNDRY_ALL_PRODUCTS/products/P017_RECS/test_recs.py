import unittest

if __package__:
    from .parents.csid import Safeguard
else:
    from parents.csid import Safeguard
if __package__:
    from .parents.rel import ConsistencyRelation, EvidenceRecord
else:
    from parents.rel import ConsistencyRelation, EvidenceRecord
if __package__:
    from .recs import RelationalEvidenceConditionedSafeguards
else:
    from recs import RelationalEvidenceConditionedSafeguards


class RECSTests(unittest.TestCase):
    def fixture(self):
        records = [
            EvidenceRecord("invoice", "i", 100.0, 0.02),
            EvidenceRecord("warehouse", "w", 40.0, 0.02),
            EvidenceRecord("carrier", "c", 100.0, 0.02),
        ]
        relations = [
            ConsistencyRelation("invoice_vs_warehouse", "invoice", "warehouse", 5.0),
            ConsistencyRelation("warehouse_vs_carrier", "warehouse", "carrier", 5.0),
            ConsistencyRelation("invoice_vs_carrier", "invoice", "carrier", 5.0),
        ]
        safeguards = [
            Safeguard("warehouse_independent_audit", 30.0, "independent", {"warehouse": 0.95}),
            Safeguard("invoice_check", 30.0, "invoice", {"invoice": 0.8}),
        ]
        return records, relations, safeguards

    def test_localizes_middle_record_and_routes_guard(self):
        records, relations, safeguards = self.fixture()
        result = RelationalEvidenceConditionedSafeguards().design(
            records=records,
            relations=relations,
            consequences={"invoice": 100.0, "warehouse": 500.0, "carrier": 100.0},
            safeguards=safeguards,
            budget=30.0,
        )
        self.assertGreater(result["posterior_culprit_probability_by_record"]["warehouse"], 0.95)
        self.assertEqual(
            result["evidence_conditioned_portfolio"]["safeguards"],
            ("warehouse_independent_audit",),
        )

    def test_prior_and_posterior_are_not_conflated(self):
        records, relations, safeguards = self.fixture()
        result = RelationalEvidenceConditionedSafeguards().design(
            records=records,
            relations=relations,
            consequences={"invoice": 100.0, "warehouse": 500.0, "carrier": 100.0},
            safeguards=safeguards,
            budget=30.0,
        )
        self.assertNotEqual(result["prior_portfolio"], result["evidence_conditioned_portfolio"])
        self.assertIn("conditional", result["posterior_semantics"])

    def test_names_must_match_exactly(self):
        records, relations, safeguards = self.fixture()
        with self.assertRaises(ValueError):
            RelationalEvidenceConditionedSafeguards().design(
                records=records,
                relations=relations,
                consequences={"invoice": 1.0},
                safeguards=safeguards,
                budget=30.0,
            )

    def test_duplicate_evidence_family_is_not_double_counted(self):
        records, relations, _ = self.fixture()
        safeguards = [
            Safeguard("a", 10.0, "same", {"warehouse": 0.6}),
            Safeguard("b", 10.0, "same", {"warehouse": 0.7}),
        ]
        result = RelationalEvidenceConditionedSafeguards().design(
            records=records,
            relations=relations,
            consequences={"invoice": 0.0, "warehouse": 1000.0, "carrier": 0.0},
            safeguards=safeguards,
            budget=20.0,
        )
        self.assertLessEqual(
            result["evidence_conditioned_portfolio"]["coverage_by_failure"]["warehouse"],
            0.7,
        )


if __name__ == "__main__":
    unittest.main()
