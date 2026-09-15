import unittest
from bmdre import belief_metric_explore as f
class T(unittest.TestCase):
 def test_safe(self): self.assertTrue(f(tipping_distance=.1,approximation_error=.01).use_reduced)
 def test_tip(self): self.assertFalse(f(tipping_distance=.03,approximation_error=.03).use_reduced)
 def test_over(self): self.assertFalse(f(tipping_distance=.03,approximation_error=.04).use_reduced)
 def test_zero_error(self): self.assertTrue(f(tipping_distance=.01,approximation_error=0).use_reduced)
 def test_negative(self):
  with self.assertRaises(ValueError): f(tipping_distance=-1,approximation_error=0)
 def test_comparator(self): self.assertFalse(f(tipping_distance=.02,approximation_error=.05).use_reduced)
if __name__=='__main__': unittest.main()
