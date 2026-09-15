import unittest
from stha import support_tipped_holdout as f
class T(unittest.TestCase):
 def test_abstain(self): self.assertIsNone(f(losses={'a':1,'b':0},ess_fraction=.4,support_floor=.5).selected)
 def test_select(self): self.assertEqual(f(losses={'a':1,'b':0},ess_fraction=.6,support_floor=.5).selected,'b')
 def test_equal_floor(self): self.assertEqual(f(losses={'a':1},ess_fraction=.5,support_floor=.5).selected,'a')
 def test_empty(self): self.assertIsNone(f(losses={},ess_fraction=.8,support_floor=.5).selected)
 def test_bad_fraction(self):
  with self.assertRaises(ValueError): f(losses={},ess_fraction=2,support_floor=.5)
 def test_comparator_diff(self): self.assertIsNone(f(losses={'winner':0},ess_fraction=.1,support_floor=.5).selected)
if __name__=='__main__': unittest.main()
