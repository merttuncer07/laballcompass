import unittest
from bvrp import boundary_viability_plan as f
class T(unittest.TestCase):
 def test_nominal(self): self.assertEqual(f(lower_action='go',upper_action='go',nominal_action='go',safe_fallback='hold').action,'go')
 def test_fallback(self): self.assertEqual(f(lower_action='go',upper_action='avoid',nominal_action='go',safe_fallback='hold').action,'hold')
 def test_flag(self): self.assertTrue(f(lower_action='go',upper_action='avoid',nominal_action='go',safe_fallback='hold').fallback_used)
 def test_no_flag(self): self.assertFalse(f(lower_action='go',upper_action='go',nominal_action='go',safe_fallback='hold').fallback_used)
 def test_empty(self):
  with self.assertRaises(ValueError): f(lower_action='a',upper_action='b',nominal_action='',safe_fallback='h')
 def test_comparator_diff(self): self.assertNotEqual(f(lower_action='go',upper_action='avoid',nominal_action='go',safe_fallback='hold').action,'go')
if __name__=='__main__': unittest.main()
