
import unittest,importlib.util,pathlib,sys
from cbiaccvc import safety_boundary_information_choice
ARCH=pathlib.Path(__file__).resolve().parents[3]
C=ARCH/'02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS/IM139_IM250_CCVC/ccvc.py'; s=importlib.util.spec_from_file_location('ccvc48',C); ccvc=importlib.util.module_from_spec(s); sys.modules['ccvc48']=ccvc; s.loader.exec_module(ccvc)
PROD=ARCH/'02_FOUNDRY_ALL_PRODUCTS/products'; sys.path.insert(0,str(PROD.parent)); B=PROD/'P079_CBIA/cbia.py'; s=importlib.util.spec_from_file_location('cbia48',B); cbia=importlib.util.module_from_spec(s); sys.modules['cbia48']=cbia; s.loader.exec_module(cbia)
def case(cost=.001): return safety_boundary_information_choice(ccvc.ConservationConstrainedViability,cbia.evaluate,low_state=[.25,.75],high_state=[.75,.25],measurement_cost=cost,nominal_control=.8,step=.1)
class T(unittest.TestCase):
 def test_boundary(self): self.assertTrue(case()['action_boundary_crossed'])
 def test_measure(self): self.assertTrue(case()['measurement_used'])
 def test_controls_differ(self): self.assertNotEqual(case()['low_safe_control'],case()['high_safe_control'])
 def test_removal_violates(self): self.assertGreater(case()['removal_expected_violation'],0)
 def test_resolved_safe(self): self.assertAlmostEqual(case()['resolved_expected_violation'],0,places=8)
 def test_gain_after_cost(self): self.assertGreater(case()['gain_vs_removed_information'],0)
 def test_expensive_measure_skipped(self): self.assertFalse(case(cost=.1)['measurement_used'])
 def test_reproducible(self): self.assertEqual(case(),case())
if __name__=='__main__': unittest.main()
