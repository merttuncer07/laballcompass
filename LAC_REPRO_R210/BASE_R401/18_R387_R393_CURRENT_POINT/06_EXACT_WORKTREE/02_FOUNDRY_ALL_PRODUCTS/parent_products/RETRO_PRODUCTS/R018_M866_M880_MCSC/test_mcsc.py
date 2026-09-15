import unittest, numpy as np
from mcsc import certify_monotone_comparative_statics
class Tests(unittest.TestCase):
 def test_increasing_differences_certified(self):
  a=np.arange(5.);t=np.arange(4.);u=np.array([[th*x-x*x for th in t] for x in a]);r=certify_monotone_comparative_statics(a,t,u);self.assertTrue(r.increasing_differences);self.assertEqual(r.certified_direction,"NONDECREASING")
 def test_optimal_selections_move_up(self):
  a=np.arange(5.);t=np.arange(5.);u=np.array([[th*x-.5*x*x for th in t] for x in a]);r=certify_monotone_comparative_statics(a,t,u);self.assertTrue(r.least_selection_nondecreasing);self.assertTrue(r.greatest_selection_nondecreasing)
 def test_failure_returns_witness(self):
  r=certify_monotone_comparative_statics([0,1],[0,1],[[0,0],[1,-1]]);self.assertFalse(r.increasing_differences);self.assertIsNotNone(r.increasing_violation_witness)
 def test_unsorted_actions_rejected(self):
  with self.assertRaises(ValueError):certify_monotone_comparative_statics([1,0],[0,1],[[0,0],[0,0]])
if __name__=="__main__":unittest.main()
