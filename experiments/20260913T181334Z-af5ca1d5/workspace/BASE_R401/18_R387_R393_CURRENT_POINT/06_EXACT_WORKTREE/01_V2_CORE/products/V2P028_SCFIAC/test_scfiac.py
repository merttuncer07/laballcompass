import unittest
from scfiac import support_constrained_firewall as f
class T(unittest.TestCase):
 def test_suspect_block(self): self.assertEqual(f(channels=[('bad',10,True,True),('safe',2,False,True)]).choice,'safe')
 def test_support_block(self): self.assertEqual(f(channels=[('unsupported',10,False,False),('safe',2,False,True)]).choice,'safe')
 def test_best_safe(self): self.assertEqual(f(channels=[('a',1,False,True),('b',2,False,True)]).choice,'b')
 def test_none(self): self.assertIsNone(f(channels=[('a',1,False,False)]).choice)
 def test_lists(self): self.assertIn('a',f(channels=[('a',1,True,False)]).blocked_suspect)
 def test_comparator_diff(self): self.assertNotEqual(f(channels=[('nominal_best',99,False,False),('supported',1,False,True)]).choice,'nominal_best')
if __name__=='__main__': unittest.main()
