
import unittest, importlib.util, pathlib, sys
from pipeg import producer_incentive_aware_persuasion
ARCH=pathlib.Path(__file__).resolve().parents[3]
B=ARCH/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R001_C313_BPISD/bpisd.py'
s=importlib.util.spec_from_file_location('bpisd_v44',B); b=importlib.util.module_from_spec(s); sys.modules['bpisd_v44']=b; s.loader.exec_module(b)
P=ARCH/'03_LCB_EXECUTABLE_AND_EVIDENCE/prototypes/LABCOMPASS__LCB-7F3A91__20260825-1048-TR__PRODUCT_PROTOTYPES__r38.py'
s=importlib.util.spec_from_file_location('lcb_v44',P); l=importlib.util.module_from_spec(s); sys.modules['lcb_v44']=l; s.loader.exec_module(l)
def case(weight=.5,disclosure=.8):
 return producer_incentive_aware_persuasion(b.design_binary_persuasion,l.InformationProductionEquilibriumGuardV0.equilibrium,
   prior_state_one=.3,action_names=['REJECT','ADOPT'],receiver_payoffs=[[0,0],[-1.5,1]],sender_payoffs=[[0,0],[1,1]],
   base_copy_friction=.8,disclosure_to_friction=disclosure,producer_values=[1,1,1],producer_costs=[.55,.55,.55],spillover=.1,
   future_information_weight=weight)
class T(unittest.TestCase):
 def test_unrestricted_persuasion_is_current_payoff_choice(self): self.assertEqual(case()['mechanism_removed_choice'],'PERSUASION')
 def test_externality_changes_choice(self): self.assertEqual(case()['candidate_choice'],'NO_INFORMATION')
 def test_persuasion_kills_entry_in_declared_shell(self): self.assertEqual(case()['persuasion_active_producers'],0)
 def test_noinfo_preserves_entry(self): self.assertEqual(case()['noinfo_active_producers'],3)
 def test_composition_gain_positive(self): self.assertGreater(case()['gain_vs_removed_production_externality'],.15)
 def test_zero_future_weight_collapses(self): self.assertEqual(case(weight=0)['candidate_choice'],'PERSUASION')
 def test_zero_disclosure_effect_collapses(self): self.assertEqual(case(disclosure=0)['candidate_choice'],'PERSUASION')
 def test_reproducible(self): self.assertEqual(case(),case())
if __name__=='__main__': unittest.main()
