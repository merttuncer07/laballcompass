import unittest
from bosaro import support_aware_robust_optimizer as f
class T(unittest.TestCase):
 def base(self): return dict(mean=[.12,.10],shift_direction=[1,0],base_shift_radius=.02,support_fraction=.25,risk_penalty=.001,grid_step=.01)
 def test_radius_inflates(self): self.assertAlmostEqual(f(**self.base()).support_radius,.04)
 def test_fragile_exposure_reduced(self):
  r=f(**self.base()); self.assertLessEqual(r.weights[0],r.base_radius_weights[0])
 def test_full_support_base_radius(self):
  a=self.base();a['support_fraction']=1; r=f(**a); self.assertAlmostEqual(r.support_radius,a['base_shift_radius'])
 def test_weights_sum_one(self): self.assertAlmostEqual(sum(f(**self.base()).weights),1)
 def test_direction_exposure_matches(self): self.assertAlmostEqual(f(**self.base()).fragile_direction_exposure,f(**self.base()).weights[0])
 def test_bad_support(self):
  a=self.base();a['support_fraction']=0
  with self.assertRaises(ValueError): f(**a)
 def test_shape(self):
  a=self.base();a['mean']=[1,2,3]
  with self.assertRaises(ValueError): f(**a)
 def test_status(self): self.assertIn('SUPPORT_INFLATED',f(**self.base()).status)
if __name__=='__main__': unittest.main()
