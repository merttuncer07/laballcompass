import unittest
from spitwmr import search_policy_targeted_reduction as f
class T(unittest.TestCase):
 def args(self): return dict(system_matrix=[[.95,0,0],[0,.8,0],[0,0,.6]],input_matrix=[[10],[1],[1]],state_names=['energy','policy','minor'],policy_sensitivity=[0,5,.1],retain_count=1,horizon=15)
 def test_policy_state_retained(self): self.assertEqual(f(**self.args()).reduction['retained_states'],('policy',))
 def test_energy_baseline_differs(self): self.assertEqual(f(**self.args()).energy_baseline['retained_states'],('energy',))
 def test_target_error_better(self): self.assertGreater(f(**self.args()).relative_error_gain,0)
 def test_normalized_target(self):
  r=f(**self.args()); self.assertAlmostEqual(sum(x*x for x in r.policy_target),1)
 def test_zero_target_rejected(self):
  a=self.args(); a['policy_sensitivity']=[0,0,0]
  with self.assertRaises(ValueError): f(**a)
 def test_shape_rejected(self):
  a=self.args(); a['policy_sensitivity']=[1,2]
  with self.assertRaises(ValueError): f(**a)
 def test_full_retention_zero_error(self):
  a=self.args(); a['retain_count']=3; self.assertAlmostEqual(f(**a).reduction['relative_target_error'],0)
 def test_status(self): self.assertIn('POLICY_TARGET',f(**self.args()).status)
if __name__=='__main__': unittest.main()
