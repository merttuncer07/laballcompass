
import unittest, importlib.util, pathlib, sys
from cbscg import boundary_information_capacity_choice
ARCH=pathlib.Path(__file__).resolve().parents[3]
P=ARCH/'03_LCB_EXECUTABLE_AND_EVIDENCE/prototypes/LABCOMPASS__LCB-7F3A91__20260825-1048-TR__PRODUCT_PROTOTYPES__r38.py'
s=importlib.util.spec_from_file_location('lcb_r38_v43',P); lcb=importlib.util.module_from_spec(s); sys.modules['lcb_r38_v43']=lcb; s.loader.exec_module(lcb)
PROD=ARCH/'02_FOUNDRY_ALL_PRODUCTS/products'; sys.path.insert(0,str(PROD.parent))
# spec_runtime imports as products.spec_runtime; parent folder exposes products package
C=PROD/'P079_CBIA/cbia.py'; s=importlib.util.spec_from_file_location('cbia_v43',C); cbia=importlib.util.module_from_spec(s); sys.modules['cbia_v43']=cbia; s.loader.exec_module(cbia)
INC=[[1,0],[0,1]]
PROJECTS={
 'A':{'slopes':[0.7994258,0.8906196],'intercepts':[2.99162981,2.94250602]},
 'B':{'slopes':[1.3076932,0.8906196],'intercepts':[2.99162981,1.57167932]},
}
def case(cost=.02,projects=PROJECTS): return boundary_information_capacity_choice(lcb.StrategicCapacityResponseGuardV0,cbia.evaluate,INC,projects,low_demand=4,high_demand=9,high_probability=.5,measurement_cost=cost)
class T(unittest.TestCase):
 def test_strategic_response_creates_action_boundary(self): self.assertTrue(case()['action_boundary_crossed'])
 def test_cbia_selects_measurement(self): self.assertTrue(case()['measurement_used'])
 def test_information_gain_survives_cost(self): self.assertGreater(case()['gain_vs_removed_information_acquisition'],.04)
 def test_low_and_high_actions_differ(self): self.assertNotEqual(case()['low_best'],case()['high_best'])
 def test_expensive_measurement_is_skipped(self): self.assertFalse(case(cost=.2)['measurement_used'])
 def test_no_boundary_no_measurement(self):
  q={'A':{'slopes':[.5,1.0],'intercepts':[1,3]},'B':{'slopes':[1.5,1.0],'intercepts':[3,3]}}
  self.assertFalse(case(projects=q)['measurement_used'])
 def test_invalid_cost(self):
  with self.assertRaises(ValueError): case(cost=-1)
 def test_reproducible(self): self.assertEqual(case(),case())
if __name__=='__main__': unittest.main()
