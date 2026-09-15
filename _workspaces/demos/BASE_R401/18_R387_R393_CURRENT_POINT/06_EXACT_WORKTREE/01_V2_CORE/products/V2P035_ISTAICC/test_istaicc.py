import unittest
from istaicc import *
class T(unittest.TestCase):
 def channels(self): return [Channel('trigger',.04,.08,.02),Channel('myopic',.06,.04,.4)]
 def test_immediate_prefers_myopic(self): self.assertEqual(tipping_aware_information_acquisition(self.channels(),base_friction=.4,network_strength=.9,temperature=.08,future_opportunity_value=.5).immediate_choice,'myopic')
 def test_tipping_can_choose_trigger(self): self.assertEqual(tipping_aware_information_acquisition(self.channels(),base_friction=.4,network_strength=.9,temperature=.08,future_opportunity_value=.5).chosen,'trigger')
 def test_equilibria_reported(self): self.assertTrue(tipping_aware_information_acquisition(self.channels(),base_friction=.4,network_strength=.9,temperature=.08,future_opportunity_value=.5).equilibria['trigger'])
 def test_zero_future_reverts_to_immediate(self):
  r=tipping_aware_information_acquisition(self.channels(),base_friction=.4,network_strength=.9,temperature=.08,future_opportunity_value=0); self.assertEqual(r.chosen,r.immediate_choice)
 def test_high_cost_skips(self):
  r=tipping_aware_information_acquisition([Channel('x',0,10,.5)],base_friction=.4,network_strength=.1,temperature=.1,future_opportunity_value=0); self.assertIsNone(r.chosen)
 def test_bad_temp(self):
  with self.assertRaises(ValueError): tipping_aware_information_acquisition(self.channels(),base_friction=.4,network_strength=.9,temperature=0,future_opportunity_value=.5)
 def test_negative_value_rejected(self):
  with self.assertRaises(ValueError): tipping_aware_information_acquisition(self.channels(),base_friction=-1,network_strength=.9,temperature=.1,future_opportunity_value=.5)
 def test_status(self): self.assertIn('TIPPING',tipping_aware_information_acquisition(self.channels(),base_friction=.4,network_strength=.9,temperature=.08,future_opportunity_value=.5).status)
if __name__=='__main__': unittest.main()
