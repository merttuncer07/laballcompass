import unittest
from ccdre import conservation_calibrated_explore as f
class T(unittest.TestCase):
 def test_blocks_high_value(self): self.assertEqual(f(channels=[('bad',10,.5),('safe',3,.01)],residual_limit=.1).choice,'safe')
 def test_all_good(self): self.assertEqual(f(channels=[('a',1,0),('b',2,.1)],residual_limit=.1).choice,'b')
 def test_none(self): self.assertIsNone(f(channels=[('a',1,.2)],residual_limit=.1).choice)
 def test_block_list(self): self.assertIn('bad',f(channels=[('bad',10,.5),('safe',3,0)],residual_limit=.1).blocked)
 def test_negative_limit(self):
  with self.assertRaises(ValueError): f(channels=[],residual_limit=-1)
 def test_comparator_diff(self): self.assertNotEqual(f(channels=[('bad',10,.5),('safe',3,0)],residual_limit=.1).choice,'bad')
if __name__=='__main__': unittest.main()
