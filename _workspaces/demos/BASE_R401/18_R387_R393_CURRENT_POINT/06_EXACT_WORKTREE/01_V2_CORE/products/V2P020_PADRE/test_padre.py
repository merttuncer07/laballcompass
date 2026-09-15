import unittest
from padre import privacy_accuracy_explore as f
class T(unittest.TestCase):
 def test_low_epsilon_blocks(self): self.assertFalse(f(epsilon=.1,margin=1,sensitivity=1,target=.9,channel='p').usable)
 def test_high_epsilon_allows(self): self.assertTrue(f(epsilon=3,margin=1,sensitivity=1,target=.9,channel='p').usable)
 def test_block_choice_none(self): self.assertIsNone(f(epsilon=.1,margin=1,sensitivity=1,target=.9,channel='p').choice)
 def test_allow_choice(self): self.assertEqual(f(epsilon=3,margin=1,sensitivity=1,target=.9,channel='p').choice,'p')
 def test_invalid(self):
  with self.assertRaises(ValueError): f(epsilon=-1,margin=1,sensitivity=1,target=.9,channel='p')
 def test_monotone(self): self.assertLess(f(epsilon=.5,margin=1,sensitivity=1,target=.9,channel='p').correctness,f(epsilon=2,margin=1,sensitivity=1,target=.9,channel='p').correctness)
if __name__=='__main__': unittest.main()
