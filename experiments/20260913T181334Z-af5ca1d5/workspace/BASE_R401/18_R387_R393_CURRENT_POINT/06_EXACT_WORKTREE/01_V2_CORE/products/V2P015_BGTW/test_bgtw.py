import unittest
from bgtw import boundary_gated_wealth as f
class T(unittest.TestCase):
 def test_preserve(self): self.assertEqual(f(wealth=5,price=1,lower_action=1,upper_action=1).wealth_after,5)
 def test_spend(self): self.assertEqual(f(wealth=5,price=1,lower_action=0,upper_action=1).wealth_after,4)
 def test_insufficient(self): self.assertFalse(f(wealth=.5,price=1,lower_action=0,upper_action=1).test)
 def test_exact(self): self.assertEqual(f(wealth=1,price=1,lower_action=0,upper_action=1).wealth_after,0)
 def test_negative(self):
  with self.assertRaises(ValueError): f(wealth=-1,price=1,lower_action=0,upper_action=1)
 def test_mechanism_removal(self): self.assertEqual(f(wealth=2,price=1,lower_action=1,upper_action=1).spent,0)
if __name__=='__main__': unittest.main()
