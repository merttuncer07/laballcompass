
import unittest, importlib.util, pathlib, sys
from atscwc import compare_active_vs_fixed
ARCH=pathlib.Path(__file__).resolve().parents[3]
P=ARCH/'03_LCB_EXECUTABLE_AND_EVIDENCE/prototypes/LABCOMPASS__LCB-7F3A91__20260825-1048-TR__PRODUCT_PROTOTYPES__r38.py'
s=importlib.util.spec_from_file_location('lcb_r38_v42',P); lcb=importlib.util.module_from_spec(s); sys.modules['lcb_r38_v42']=lcb; s.loader.exec_module(lcb)
C=ARCH/'02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS/IM340_IM280_CWC/cwc.py'
s=importlib.util.spec_from_file_location('cwc_v42',C); cwc=importlib.util.module_from_spec(s); sys.modules['cwc_v42']=cwc; s.loader.exec_module(cwc)
def case(): return compare_active_vs_fixed(lcb.ActiveThresholdSensingV0,cwc.CalibrationWidthController,cwc.summarize,query_budget=6,tasks=500,seed=0)
class T(unittest.TestCase):
 def test_interval_score_improves(self): self.assertGreater(case()['interval_score_gain'],2.0)
 def test_width_reduces(self): self.assertGreater(case()['mean_width_reduction'],4.0)
 def test_coverage_rmse_improves(self): self.assertGreater(case()['rolling_coverage_rmse_gain'],0)
 def test_target_coverage_preserved(self): self.assertLess(abs(case()['active']['coverage']-.9),.02)
 def test_active_status(self): self.assertIn('IMPROVES',case()['status'])
 def test_reproducible(self): self.assertEqual(case(),case())
 def test_bad_budget(self):
  with self.assertRaises(ValueError): compare_active_vs_fixed(lcb.ActiveThresholdSensingV0,cwc.CalibrationWidthController,cwc.summarize,query_budget=31)
 def test_uninformative_accuracy_rejected(self):
  with self.assertRaises(ValueError): compare_active_vs_fixed(lcb.ActiveThresholdSensingV0,cwc.CalibrationWidthController,cwc.summarize,response_accuracy=.5)
if __name__=='__main__': unittest.main()
