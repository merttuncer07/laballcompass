import unittest
from codre import causal_overlap_explore as f
class T(unittest.TestCase):
 def test_blocks_unsupported(self): self.assertEqual(f(candidates=[('bad',10,.1),('safe',2,.8)],overlap_floor=.5).choice,'safe')
 def test_all_good(self): self.assertEqual(f(candidates=[('a',1,.8),('b',2,.7)],overlap_floor=.5).choice,'b')
 def test_none(self): self.assertIsNone(f(candidates=[('a',1,.2)],overlap_floor=.5).choice)
 def test_rejected(self): self.assertIn('a',f(candidates=[('a',1,.2)],overlap_floor=.5).rejected)
 def test_invalid(self):
  with self.assertRaises(ValueError): f(candidates=[],overlap_floor=2)
 def test_comparator_diff(self): self.assertNotEqual(f(candidates=[('unsupported_high',10,.1),('supported',1,.9)],overlap_floor=.5).choice,'unsupported_high')
if __name__=='__main__': unittest.main()
