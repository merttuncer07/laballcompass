
import unittest, importlib.util, pathlib, sys, numpy as np
from mtcwc import compare
ARCH=pathlib.Path(__file__).resolve().parents[3]
S=ARCH/'02_FOUNDRY_ALL_PRODUCTS/products/shared_foundry.py'; s=importlib.util.spec_from_file_location('sf_v46',S); sf=importlib.util.module_from_spec(s); sys.modules['sf_v46']=sf; s.loader.exec_module(sf)
C=ARCH/'02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS/IM340_IM280_CWC/cwc.py'; s=importlib.util.spec_from_file_location('cwc_v46',C); cwc=importlib.util.module_from_spec(s); sys.modules['cwc_v46']=cwc; s.loader.exec_module(cwc)
def case(): return compare(sf.mcst,cwc.CalibrationWidthController,cwc.summarize,np.r_[np.ones(100),np.full(100,2.5)],seed=2)
class T(unittest.TestCase):
 def test_tipping_exists(self): self.assertIsNotNone(case()['candidate']['tipping_value'])
 def test_one_reset(self): self.assertEqual(case()['candidate']['resets'],1)
 def test_removal_has_no_reset(self): self.assertEqual(case()['mechanism_removed']['resets'],0)
 def test_interval_score_gain(self): self.assertGreater(case()['interval_score_gain'],.8)
 def test_coverage_rmse_gain(self): self.assertGreater(case()['rolling_coverage_rmse_gain'],.05)
 def test_post_shift_coverage_gain(self): self.assertGreater(case()['post_shift_coverage_gain'],.3)
 def test_no_shift_collapses(self):
  r=compare(sf.mcst,cwc.CalibrationWidthController,cwc.summarize,np.ones(200),seed=2); self.assertEqual(r['candidate']['resets'],0); self.assertAlmostEqual(r['interval_score_gain'],0)
 def test_reproducible(self): self.assertEqual(case(),case())
if __name__=='__main__': unittest.main()
