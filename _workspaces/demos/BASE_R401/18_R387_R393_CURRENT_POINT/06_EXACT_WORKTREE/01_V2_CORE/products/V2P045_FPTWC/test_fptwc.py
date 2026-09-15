
import unittest, importlib.util, pathlib, sys
from fptwc import tipping_aware_testing_wealth
ARCH=pathlib.Path(__file__).resolve().parents[3]
F=ARCH/'02_FOUNDRY_ALL_PRODUCTS/products/P030_FPTE/fpte.py'
s=importlib.util.spec_from_file_location('fpte_v45',F); f=importlib.util.module_from_spec(s); sys.modules['fpte_v45']=f; s.loader.exec_module(f)
P=ARCH/'03_LCB_EXECUTABLE_AND_EVIDENCE/prototypes/LABCOMPASS__LCB-7F3A91__20260825-1048-TR__PRODUCT_PROTOTYPES__r38.py'
s=importlib.util.spec_from_file_location('lcb_v45',P); l=importlib.util.module_from_spec(s); sys.modules['lcb_v45']=l; s.loader.exec_module(l)
MECH=[f.FailureMechanism('m1',.5,10),f.FailureMechanism('m2',.55,10),f.FailureMechanism('m3',.6,10)]
PVAL=[.065,.03,.04,.2,.3,.4,.5,.8,.9,.7]
def case(base=.95): return tipping_aware_testing_wealth(f.explore_retention_tipping,f.FailureMechanism,l.TestingWealthControllerV0,mechanisms=MECH,baseline_retention=base,retention_grid=[.95,.9,.85,.8,.75,.7,.65,.6,.55,.5],required_energy=18,p_values=PVAL)
class T(unittest.TestCase):
 def test_tipping_found(self): self.assertIn('TIPPING_FOUND',case()['tipping_status'])
 def test_near_tipping_frontloads(self): self.assertEqual(case()['candidate']['gamma_power'],2.5)
 def test_removal_stays_baseline(self): self.assertEqual(case()['mechanism_removed']['gamma_power'],1.6)
 def test_discovery_gain(self): self.assertGreaterEqual(case()['discovery_gain'],3)
 def test_same_pvalue_stream(self): self.assertEqual(len(case()['candidate']['trajectory']),len(case()['mechanism_removed']['trajectory']))
 def test_far_tipping_collapses(self):
  # move the decision point far from the nearest failure threshold
  r=tipping_aware_testing_wealth(f.explore_retention_tipping,f.FailureMechanism,l.TestingWealthControllerV0,mechanisms=MECH,baseline_retention=.99,retention_grid=[.8,.7,.6,.5],required_energy=18,p_values=PVAL,proximity_threshold=.1)
  self.assertEqual(r['candidate']['gamma_power'],1.6)
 def test_status_changes_only_when_coupled(self): self.assertIn('REALLOCATES',case()['status'])
 def test_reproducible(self): self.assertEqual(case(),case())
if __name__=='__main__': unittest.main()
