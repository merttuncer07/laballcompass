import unittest
import numpy as np
from atrc import control_memory_retention


def stream(n=180):
    rng=np.random.default_rng(45); categories=np.arange(n)%12
    categories[categories>1]=0
    x=np.column_stack((categories==0,categories==1,np.sin(np.arange(n)/20)))
    y=np.where(categories==1,5.0,1.0+.4*np.sin(np.arange(n)/20))+rng.normal(0,.05,n)
    return x,y

class Tests(unittest.TestCase):
    def test_budget_is_never_exceeded(self):
        r=control_memory_retention(*stream(),memory_budget=10,audit_horizon=30,neighbors=2,age_penalty=1e-5)
        self.assertEqual(r.budget_violations,0); self.assertLessEqual(r.maximum_realized_memory,10)
    def test_target_aware_retention_beats_fifo_on_rare_context(self):
        r=control_memory_retention(*stream(),memory_budget=10,audit_horizon=30,neighbors=2,age_penalty=1e-5)
        self.assertLess(r.target_aware_rmse,r.fifo_rmse)
    def test_every_eviction_preserves_exact_budget(self):
        r=control_memory_retention(*stream(50),memory_budget=8,audit_horizon=20)
        self.assertTrue(all(len(e.retained_indices)==8 for e in r.evictions))
    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError): control_memory_retention(*stream(),memory_budget=1,audit_horizon=10)
if __name__=='__main__': unittest.main()
