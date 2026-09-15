import unittest, numpy as np
from sccatf import support_covariance_coupled_allocation as f
R=[{'time_weight':10,'frequency_weight':1},{'time_weight':1,'frequency_weight':10}]
O=[{'name':'short','time_spread':1,'frequency_spread':4,'cost':2,'support_exposure':2.0},{'name':'long','time_spread':4,'frequency_spread':1,'cost':2,'support_exposure':.1}]
C=np.array([[1,.95],[.95,1]])
class T(unittest.TestCase):
 def test_low_coupling_collapses_to_control(self):
  r=f(R,O,C,budget=4,coupling_penalty=8); self.assertEqual(r['allocation'],r['control_allocation']); self.assertAlmostEqual(r['gain_vs_removed_mechanism'],0)
 def test_high_coupling_changes_allocation(self):
  r=f(R,O,C,budget=4,coupling_penalty=160); self.assertNotEqual(r['allocation'],r['control_allocation']); self.assertGreater(r['gain_vs_removed_mechanism'],0)
 def test_zero_offdiagonal_reduces_to_control(self): self.assertEqual(f(R,O,np.eye(2),budget=4,coupling_penalty=160)['allocation'],f(R,O,np.eye(2),budget=4,coupling_penalty=160)['control_allocation'])
 def test_budget(self): self.assertLessEqual(f(R,O,np.eye(2),budget=4)['cost'],4)
 def test_bad_covariance_asymmetry(self):
  with self.assertRaises(ValueError): f(R,O,[[1,2],[0,1]],budget=4)
 def test_bad_covariance_indefinite(self):
  with self.assertRaises(ValueError): f(R,O,[[1,2],[2,1]],budget=4)
 def test_negative_penalty_rejected(self):
  with self.assertRaises(ValueError): f(R,O,C,budget=4,coupling_penalty=-1)
 def test_no_feasible_allocation_rejected(self):
  with self.assertRaises(ValueError): f(R,O,C,budget=1,coupling_penalty=160)
if __name__=='__main__': unittest.main()
