import unittest
if __package__:
    from .ratr import ReductionCandidate,select_resilience_aware_reduction
else:
    from ratr import ReductionCandidate,select_resilience_aware_reduction


class RATRTests(unittest.TestCase):
    def candidates(self): return [ReductionCandidate(('fast','aux'),0,False),ReductionCandidate(('fast','slow'),.056,True)]
    def test_hidden_risk_blocks_zero_error_choice(self): self.assertEqual(select_resilience_aware_reduction(self.candidates(),reference_alert=True,state_budget=2).selected.retained,('fast','slow'))
    def test_refuses_if_budget_too_small(self): self.assertTrue(select_resilience_aware_reduction(self.candidates(),reference_alert=True,state_budget=1).refused)
    def test_no_alert_can_choose_zero_error(self): self.assertEqual(select_resilience_aware_reduction(self.candidates(),reference_alert=False,state_budget=2).selected.target_error,0)
    def test_state_budget_enforced(self): self.assertLessEqual(len(select_resilience_aware_reduction(self.candidates(),reference_alert=True,state_budget=2).selected.retained),2)


if __name__ == '__main__': unittest.main()
