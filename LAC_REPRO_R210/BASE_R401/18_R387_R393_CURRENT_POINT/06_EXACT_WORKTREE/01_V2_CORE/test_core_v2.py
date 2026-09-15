from __future__ import annotations

import unittest

from core_v2 import (
    BenchmarkObservation,
    CapabilityRecord,
    CoreRegistry,
    EvidenceLevel,
    EvidenceVector,
    ObservationDisposition,
    ProductRole,
    CapabilityProfile,
    rank_composition,
)


class CoreV2Tests(unittest.TestCase):
    def test_comparator_loss_narrows_region_but_does_not_delete_capability(self):
        record = CapabilityRecord("K1", "AdaptiveMemory", ProductRole.BOTH)
        registry = CoreRegistry([record])
        result = record.apply(
            BenchmarkObservation(
                shell="smooth drifting time series",
                dataset_or_generator="real chronological stream",
                comparator="FIFO",
                metric="forecast utility",
                candidate_minus_comparator_utility=-0.0032,
                statistically_resolved=True,
                implementation_invariants_pass=True,
                recoverable_test_context=True,
            )
        )
        self.assertEqual(result, ObservationDisposition.NARROWS_REGION_AND_REQUIRES_ROUTER)
        self.assertEqual(len(registry), 1)
        self.assertIn("FIFO", registry.route("K1", qualified_region=False))

    def test_implementation_failure_is_not_theory_death(self):
        record = CapabilityRecord("K2", "FiberSampler", ProductRole.STANDALONE)
        result = record.apply(
            BenchmarkObservation(
                shell="large sparse fiber",
                dataset_or_generator="synthetic",
                comparator="exact enumeration",
                metric="total variation",
                candidate_minus_comparator_utility=None,
                statistically_resolved=False,
                implementation_invariants_pass=False,
                recoverable_test_context=True,
                notes="constraint-preservation bug",
            )
        )
        self.assertEqual(result, ObservationDisposition.IMPLEMENTATION_REPAIR_REQUIRED)
        self.assertTrue(record.failure_regions[0].startswith("IMPLEMENTATION_DEFECT"))

    def test_product_value_and_production_readiness_are_separate(self):
        evidence = EvidenceVector(
            code_correctness=EvidenceLevel.EXECUTABLE,
            mechanism=EvidenceLevel.MECHANISM_CONTRAST,
            external_transfer=EvidenceLevel.HELD_OUT_TRANSFER,
            operational_value=EvidenceLevel.NONE,
            deployment=EvidenceLevel.NONE,
        )
        record = CapabilityRecord(
            "K3",
            "DecisionCompressor",
            ProductRole.STANDALONE,
            evidence=evidence,
            standalone_value_hypothesis="HIGH",
        )
        self.assertEqual(record.standalone_value_hypothesis, "HIGH")
        self.assertFalse(record.evidence.production_ready)

    def test_strength_can_fill_weakness_without_novelty_gate(self):
        supplier=CapabilityProfile('A','SupportAudit','FOUNDRY','ORIGINAL',frozenset({'support'}),output_types=frozenset({'gate'}),component_value=2)
        consumer=CapabilityProfile('B','Allocator','LCB','EXECUTABLE',weakness_tags=frozenset({'support'}),input_types=frozenset({'gate'}),standalone_value=3)
        candidate=rank_composition(supplier,consumer)
        self.assertIsNotNone(candidate)
        self.assertIn('support',candidate.addressed_weaknesses)
        self.assertGreater(candidate.score,10)

    def test_incompatible_pair_is_not_forced(self):
        a=CapabilityProfile('A','A','X','E',output_types=frozenset({'state'}))
        b=CapabilityProfile('B','B','Y','E',input_types=frozenset({'legal_contract'}))
        self.assertIsNone(rank_composition(a,b))


if __name__ == "__main__":
    unittest.main()
