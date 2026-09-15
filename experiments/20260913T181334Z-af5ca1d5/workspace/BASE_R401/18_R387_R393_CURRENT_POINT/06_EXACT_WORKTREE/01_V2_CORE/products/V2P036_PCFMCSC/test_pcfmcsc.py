import unittest
from pcfmcsc import closure_fidelity_monotonicity as f
class T(unittest.TestCase):
 def test_monotone_pass(self): self.assertTrue(f([0,.1,.2],[.2,.1,-.1]).monotone_safe)
 def test_nonmonotone_witness(self): self.assertFalse(f([0,.1,.2],[.2,-.1,.05]).monotone_safe)
 def test_witness_exact(self): self.assertEqual(f([0,.1,.2],[.2,-.1,.05]).first_violation,(.1,.2,-.1,.05))
 def test_safe_interval(self): self.assertEqual(f([0,.1,.2],[.2,.1,-.1]).safe_intervals,((0.0,.1),))
 def test_recovery_creates_two_intervals(self): self.assertEqual(len(f([0,.1,.2,.3],[.2,-.1,.05,-.2]).safe_intervals),2)
 def test_grid_order(self):
  with self.assertRaises(ValueError): f([0,.1,.1],[1,0,-1])
 def test_bad_direction(self):
  with self.assertRaises(ValueError): f([0,1],[0,1],expected_direction='X')
 def test_status(self): self.assertIn('WITNESS',f([0,.1,.2],[.2,-.1,.05]).status)
if __name__=='__main__': unittest.main()
