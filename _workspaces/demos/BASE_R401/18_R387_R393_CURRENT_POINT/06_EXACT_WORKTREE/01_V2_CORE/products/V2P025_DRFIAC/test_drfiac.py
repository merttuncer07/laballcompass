import unittest
from drfiac import decision_relevant_firewall as f
class T(unittest.TestCase):
 def test_blocks(self): self.assertEqual(f(channels=[('bad',10,True),('safe',3,False)]).choice,'safe')
 def test_best_clean(self): self.assertEqual(f(channels=[('a',1,False),('b',2,False)]).choice,'b')
 def test_all_blocked(self): self.assertIsNone(f(channels=[('a',1,True)]).choice)
 def test_block_list(self): self.assertIn('x',f(channels=[('x',1,True)]).blocked)
 def test_empty(self): self.assertIsNone(f(channels=[]).choice)
 def test_comparator_diff(self): self.assertNotEqual(f(channels=[('contaminated',99,True),('clean',1,False)]).choice,'contaminated')
if __name__=='__main__': unittest.main()
