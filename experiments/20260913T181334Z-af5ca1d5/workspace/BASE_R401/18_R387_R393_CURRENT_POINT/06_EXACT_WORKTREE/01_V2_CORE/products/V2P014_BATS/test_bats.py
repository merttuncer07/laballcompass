import unittest
from bats import boundary_aware_timing as f
class T(unittest.TestCase):
 def test_invariant_skips(self): self.assertIsNone(f(lower_action=1,upper_action=1,timing_candidates=[(1,1)],budget=1).selected_time)
 def test_crossed_buys(self): self.assertEqual(f(lower_action=0,upper_action=1,timing_candidates=[(2,1)],budget=1).selected_time,2)
 def test_cheapest(self): self.assertEqual(f(lower_action=0,upper_action=1,timing_candidates=[(1,2),(3,1)],budget=3).selected_time,3)
 def test_budget_gate(self): self.assertIsNone(f(lower_action=0,upper_action=1,timing_candidates=[(1,2)],budget=1).selected_time)
 def test_negative_budget(self):
  with self.assertRaises(ValueError): f(lower_action=0,upper_action=1,timing_candidates=[],budget=-1)
 def test_comparator_would_spend(self): self.assertEqual(f(lower_action=1,upper_action=1,timing_candidates=[(1,.5)],budget=1).spent,0)
if __name__=='__main__': unittest.main()
