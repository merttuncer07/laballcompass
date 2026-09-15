import unittest
from vcmf import viability_constrained_multifidelity as f
class T(unittest.TestCase):
 def base(self): return dict(budget=10,fine_cost=5,cheap_cost=1,fine_variance=.04,cheap_variance=.09,cheap_bias_bound=.5,viability_margin=.1,min_fine=1)
 def test_viability_bias_respected(self): self.assertLessEqual(f(**self.base()).worst_case_bias,.1+1e-12)
 def test_requires_fine_anchor(self): self.assertGreaterEqual(f(**self.base()).fine_count,1)
 def test_unconstrained_differs(self):
  r=f(**self.base()); self.assertNotEqual((r.fine_count,r.cheap_count),r.unconstrained_choice)
 def test_unconstrained_violates_margin(self):
  r=f(**self.base()); self.assertGreater(r.unconstrained_worst_case_bias,self.base()['viability_margin'])
 def test_relaxed_margin_can_use_more_cheap(self):
  a=self.base(); a['viability_margin']=.5; self.assertGreaterEqual(f(**a).cheap_count,f(**self.base()).cheap_count)
 def test_zero_bias_matches_unconstrained_feasibility(self):
  a=self.base(); a['cheap_bias_bound']=0; r=f(**a); self.assertLessEqual(r.worst_case_bias,a['viability_margin'])
 def test_negative_rejected(self):
  a=self.base(); a['budget']=-1
  with self.assertRaises(ValueError): f(**a)
 def test_tiny_budget_rejected(self):
  a=self.base(); a['budget']=.5
  with self.assertRaises(ValueError): f(**a)
 def test_status(self): self.assertIn('VIABILITY',f(**self.base()).status)
if __name__=='__main__': unittest.main()
