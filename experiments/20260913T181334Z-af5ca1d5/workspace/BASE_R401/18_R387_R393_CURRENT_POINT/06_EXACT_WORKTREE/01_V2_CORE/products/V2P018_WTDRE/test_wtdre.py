import unittest
from wtdre import wasserstein_tipped_explore as f
class T(unittest.TestCase):
 def test_nearest(self): self.assertEqual(f(candidates=[('a',.2,1),('b',.1,1)],max_distance=1).choice,'b')
 def test_leverage(self): self.assertEqual(f(candidates=[('a',.2,4),('b',.1,1)],max_distance=1).choice,'a')
 def test_radius(self): self.assertIsNone(f(candidates=[('a',2,1)],max_distance=1).choice)
 def test_zero_leverage(self): self.assertIsNone(f(candidates=[('a',.1,0)],max_distance=1).choice)
 def test_negative_radius(self):
  with self.assertRaises(ValueError): f(candidates=[],max_distance=-1)
 def test_comparator_diff(self): self.assertEqual(f(candidates=[('highvar',.8,1),('near',.1,1)],max_distance=1).choice,'near')
if __name__=='__main__': unittest.main()
