import unittest
from sava import AuditCandidate,SharedAuditRank,allocate_verification_liquidity


class SAVATests(unittest.TestCase):
    def candidates(self):
        return [AuditCandidate('A',1.,(60,0)),AuditCandidate('B',1.,(60,40)),AuditCandidate('C',1.,(0,40))]
    def scenarios(self): return [(.70,set()),(.25,{'A'}),(.05,{'B'})]

    def test_rank_does_not_double_count_shared_pools(self):
        rank=SharedAuditRank(self.candidates(),(60,40)); self.assertEqual(rank([0,1,2]),100)

    def test_exact_posterior_selection_uses_clean_scenarios(self):
        r=allocate_verification_liquidity(self.candidates(),(60,40),self.scenarios(),audit_slots=1)
        self.assertEqual(r.mode,'EXACT_POSTERIOR_SUBSET_REOPTIMIZATION')
        self.assertEqual(r.selected_audits,('B',))

    def test_portfolio_value_is_nonadditive(self):
        r=allocate_verification_liquidity(self.candidates(),(60,40),self.scenarios())
        self.assertGreater(r.overlap_removed_value,0)
        self.assertLessEqual(sum(r.allocated_shared_capacity.values()),100)

    def test_large_candidate_set_routes_to_scalable_mode(self):
        cs=[AuditCandidate(str(i),1.,(1,)) for i in range(20)]
        r=allocate_verification_liquidity(cs,(5,),[(1,set())],audit_slots=2,exact_limit=10)
        self.assertEqual(r.mode,'SCALABLE_POLYMATROID_EXPECTED_VALUE_ALLOCATION')

    def test_invalid_scenario_mass_rejected(self):
        with self.assertRaises(ValueError): allocate_verification_liquidity(self.candidates(),(60,40),[(.5,set())])

    def test_output_keeps_every_assumption_visible(self):
        r=allocate_verification_liquidity(self.candidates(),(60,40),self.scenarios())
        self.assertIn('SHARED_CAPACITY',r.status); self.assertEqual(set(r.allocated_shared_capacity),{'A','B','C'})


if __name__=='__main__':unittest.main()
