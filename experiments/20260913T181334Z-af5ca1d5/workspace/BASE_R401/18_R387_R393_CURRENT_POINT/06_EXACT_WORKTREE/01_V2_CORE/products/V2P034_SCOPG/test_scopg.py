import unittest,numpy as np
from scopg import support_constrained_policy_backaction as f
class T(unittest.TestCase):
 def data(self):
  s=np.linspace(-1,1,20); p=(s>0).astype(float); y=2*s+.5*p; w=np.ones(20); return y,p,s,w
 def test_effect_recovered_when_supported(self): self.assertAlmostEqual(f(*self.data()).policy_effect,.5,places=6)
 def test_low_ess_abstains(self):
  y,p,s,w=self.data(); w[:]=1e-9; w[0]=1; self.assertIsNone(f(y,p,s,w,min_ess_fraction=.2).policy_effect)
 def test_collinearity_abstains(self):
  y,p,s,w=self.data(); p=s.copy(); self.assertIsNone(f(y,p,s,w,min_eigenvalue=1e-3).policy_effect)
 def test_ess_fraction_bounded(self): self.assertLessEqual(f(*self.data()).ess_fraction,1)
 def test_negative_weights_rejected(self):
  y,p,s,w=self.data(); w[0]=-1
  with self.assertRaises(ValueError): f(y,p,s,w)
 def test_shape_rejected(self):
  y,p,s,w=self.data()
  with self.assertRaises(ValueError): f(y[:-1],p,s,w)
 def test_condition_reported(self): self.assertGreater(f(*self.data()).condition_number,0)
 def test_status(self): self.assertIn('SUPPORT_CERTIFIED',f(*self.data()).status)
if __name__=='__main__': unittest.main()
