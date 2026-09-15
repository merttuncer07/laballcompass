import unittest

if __package__:
    from .reig import gate_and_borrow
else:
    from reig import gate_and_borrow
if __package__:
    from .parents.rel import ConsistencyRelation, EvidenceRecord
else:
    from parents.rel import ConsistencyRelation, EvidenceRecord
if __package__:
    from .parents.ebc import HistoricalEstimate
else:
    from parents.ebc import HistoricalEstimate


def fixture(violating=True):
    c = 1.05 if violating else 0.11
    records = [
        EvidenceRecord("A", "a", 0.10, 0.05),
        EvidenceRecord("B", "b", 0.12, 0.05),
        EvidenceRecord("C", "c", c, 0.05),
    ]
    relations = [
        ConsistencyRelation("AB", "A", "B", 0.20),
        ConsistencyRelation("AC", "A", "C", 0.20),
        ConsistencyRelation("BC", "B", "C", 0.20),
    ]
    historical = [
        HistoricalEstimate("A", 0.10, 0.15, 1.0),
        HistoricalEstimate("B", 0.12, 0.15, 1.0),
        HistoricalEstimate("C", c, 0.15, 1.0),
    ]
    return records, relations, historical


class REIGTests(unittest.TestCase):
    def test_discrepancy_localizes_and_downweights_outlier(self):
        records, relations, historical = fixture(True)
        result = gate_and_borrow(
            current_estimate=1.0,
            current_standard_error=0.5,
            evidence_records=records,
            relations=relations,
            historical=historical,
        )
        rows = {row.name: row for row in result.contributions}
        self.assertTrue(result.integrity_gate_active)
        self.assertGreater(rows["C"].conditional_suspect_probability, 0.95)
        self.assertLess(rows["C"].gated_maximum_power, 0.05)
        self.assertGreater(rows["A"].gated_maximum_power, 0.9)

    def test_gate_can_reverse_threshold_decision(self):
        records, relations, historical = fixture(True)
        result = gate_and_borrow(current_estimate=1.0, current_standard_error=0.5, evidence_records=records, relations=relations, historical=historical)
        self.assertGreater(result.ungated.posterior_estimate, 0.60)
        self.assertLess(result.gated.posterior_estimate, 0.60)

    def test_no_violation_no_penalty(self):
        records, relations, historical = fixture(False)
        result = gate_and_borrow(current_estimate=0.1, current_standard_error=0.5, evidence_records=records, relations=relations, historical=historical)
        self.assertFalse(result.integrity_gate_active)
        self.assertTrue(all(row.integrity_multiplier == 1.0 for row in result.contributions))
        self.assertAlmostEqual(result.gated.posterior_estimate, result.ungated.posterior_estimate)

    def test_conditional_semantics_explicit(self):
        records, relations, historical = fixture(True)
        result = gate_and_borrow(current_estimate=1.0, current_standard_error=0.5, evidence_records=records, relations=relations, historical=historical)
        self.assertIn("conditional", result.posterior_semantics.lower())

    def test_source_mapping_must_be_exact(self):
        records, relations, historical = fixture(True)
        bad = historical[:-1] + [HistoricalEstimate("D", 1.05, 0.15, 1.0)]
        with self.assertRaises(ValueError):
            gate_and_borrow(current_estimate=1.0, current_standard_error=0.5, evidence_records=records, relations=relations, historical=bad)

    def test_integrity_exponent_changes_policy_not_rel_posterior(self):
        records, relations, historical = fixture(True)
        soft = gate_and_borrow(current_estimate=1.0, current_standard_error=0.5, evidence_records=records, relations=relations, historical=historical, integrity_exponent=0.5)
        hard = gate_and_borrow(current_estimate=1.0, current_standard_error=0.5, evidence_records=records, relations=relations, historical=historical, integrity_exponent=2.0)
        soft_c = {row.name: row for row in soft.contributions}["C"]
        hard_c = {row.name: row for row in hard.contributions}["C"]
        self.assertAlmostEqual(
            soft_c.conditional_suspect_probability,
            hard_c.conditional_suspect_probability,
        )
        self.assertLess(hard_c.gated_maximum_power, soft_c.gated_maximum_power)


if __name__ == "__main__":
    unittest.main()
