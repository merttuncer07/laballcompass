import unittest
from sarcp import support_adjusted_reserve, realized_shortfall
class T(unittest.TestCase):
 def test_healthy_support_no_inflation(self):
  r=support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.95); self.assertAlmostEqual(r.nominal_reserve,r.support_adjusted_reserve)
 def test_fragile_support_inflates(self):
  r=support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.64); self.assertGreater(r.support_adjusted_reserve,r.nominal_reserve)
 def test_exact_floor_usable(self): self.assertFalse(support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.8).support_fragile)
 def test_lower_ess_more_reserve(self):
  a=support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.7); b=support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.4); self.assertGreater(b.support_adjusted_reserve,a.support_adjusted_reserve)
 def test_zero_sigma_stays_mean(self): self.assertEqual(support_adjusted_reserve(mean_demand=100,nominal_sigma=0,ess_fraction=.4).support_adjusted_reserve,100)
 def test_invalid_ess_zero(self):
  with self.assertRaises(ValueError): support_adjusted_reserve(mean_demand=1,nominal_sigma=1,ess_fraction=0)
 def test_invalid_ess_high(self):
  with self.assertRaises(ValueError): support_adjusted_reserve(mean_demand=1,nominal_sigma=1,ess_fraction=1.1)
 def test_negative_sigma_rejected(self):
  with self.assertRaises(ValueError): support_adjusted_reserve(mean_demand=1,nominal_sigma=-1,ess_fraction=.5)
 def test_inflation_capped(self):
  r=support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.01,max_inflation=2); self.assertAlmostEqual(r.effective_sigma,20)
 def test_mechanism_removing_comparator_shortfall(self):
  r=support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.64); demand=122; self.assertLess(realized_shortfall(r.support_adjusted_reserve,demand),realized_shortfall(r.nominal_reserve,demand))
 def test_fragile_status(self): self.assertIn('FRAGILITY',support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.64).status)
 def test_usable_status(self): self.assertIn('USABLE',support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=.95).status)
if __name__=='__main__': unittest.main()
