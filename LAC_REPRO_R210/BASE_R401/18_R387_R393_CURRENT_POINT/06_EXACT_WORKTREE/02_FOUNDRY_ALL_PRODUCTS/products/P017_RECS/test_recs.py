import unittest
import math

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
        # Independent closed-form weights for this three-record pattern,
        # including the null state. The old >.95 assertion omitted that state.
        p, q, s = .02, .98, math.exp(-.7)
        d, f = .95, .02
        null = q**3 * f**2 * (1-f)
        middle = p*q*q*s*d*d*(1-f)
        endpoints = p*p*q*s*s*d*d*(1-f)
        other_single = p*q*q*s*d*(1-d)*f
        other_pair = p*p*q*s*s*d*(1-d)*f
        expected = (middle+2*other_pair)/(null+middle+endpoints+2*other_single+2*other_pair)
        self.assertAlmostEqual(result["posterior_culprit_probability_by_record"]["warehouse"], expected)
        self.assertEqual(result["localization"]["top_candidate"]["records"], ("warehouse",))
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

    def test_repeated_checks_do_not_change_safeguard_allocation(self):
        records, relations, safeguards = self.fixture()
        repeats = relations + [ConsistencyRelation('copy_'+r.name, r.right, r.left, r.tolerance) for r in relations]
        kwargs = dict(records=records, consequences={'invoice':100.,'warehouse':500.,'carrier':100.}, safeguards=safeguards, budget=30.)
        model = RelationalEvidenceConditionedSafeguards()
        once = model.design(relations=relations, **kwargs)
        twice = model.design(relations=repeats, **kwargs)
        self.assertEqual(once['posterior_culprit_probability_by_record'],twice['posterior_culprit_probability_by_record'])
        self.assertEqual(once['evidence_conditioned_portfolio'],twice['evidence_conditioned_portfolio'])

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
