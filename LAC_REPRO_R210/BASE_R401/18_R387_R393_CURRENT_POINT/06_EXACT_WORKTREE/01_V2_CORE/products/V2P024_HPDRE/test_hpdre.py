import unittest
from hpdre import hidden_population_explore as f
class T(unittest.TestCase):
 def test_explore(self): self.assertTrue(f(action_margin=.1,hidden_mass=.2,max_effect_per_mass=1).explore_hidden)
 def test_skip(self): self.assertFalse(f(action_margin=.5,hidden_mass=.2,max_effect_per_mass=1).explore_hidden)
 def test_equal(self): self.assertTrue(f(action_margin=.2,hidden_mass=.2,max_effect_per_mass=1).explore_hidden)
 def test_bound(self): self.assertAlmostEqual(f(action_margin=.1,hidden_mass=.2,max_effect_per_mass=3).hidden_effect_bound,.6)
 def test_invalid(self):
  with self.assertRaises(ValueError): f(action_margin=.1,hidden_mass=2,max_effect_per_mass=1)
 def test_comparator(self): self.assertTrue(f(action_margin=.05,hidden_mass=.1,max_effect_per_mass=1).explore_hidden)
if __name__=='__main__': unittest.main()
