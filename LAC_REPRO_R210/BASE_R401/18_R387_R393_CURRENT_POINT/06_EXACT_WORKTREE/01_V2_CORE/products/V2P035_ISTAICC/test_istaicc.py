import math
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
 def test_paid_no_effect_channel_only_scores_cost(self):
  for start in (0.,.2,.9):
   with self.subTest(current_participation=start):
    r=tipping_aware_information_acquisition([Channel('none',0,.01,.1)],base_friction=.1,network_strength=.9,temperature=.08,future_opportunity_value=1.,current_participation=start)
    self.assertAlmostEqual(r.channel_scores['none'],-.01)
    self.assertIsNone(r.chosen)
 def test_score_depends_on_baseline_friction(self):
  scores=[]
  for friction in (.1,.2,.4):
   with self.subTest(base_friction=friction):
    r=tipping_aware_information_acquisition([Channel('x',0,.01,.2)],base_friction=friction,network_strength=0,temperature=.1,future_opportunity_value=.5)
    expected=-.01+.5*(1/(1+math.exp(2))-1/(1+math.exp(friction/.1)))
    self.assertAlmostEqual(r.channel_scores['x'],expected)
    self.assertEqual(r.chosen,'x' if expected>0 else None)
    scores.append(r.channel_scores['x'])
  self.assertLess(scores[0],scores[1])
  self.assertLess(scores[1],scores[2])
 def test_negative_incremental_participation_reduces_score(self):
  for start in (0.,.9):
   with self.subTest(current_participation=start):
    r=tipping_aware_information_acquisition([Channel('harmful',.1,.02,.5)],base_friction=.1,network_strength=0,temperature=.1,future_opportunity_value=1.,current_participation=start)
    expected=.08+1/(1+math.exp(4))-1/(1+math.exp(1))
    self.assertAlmostEqual(r.channel_scores['harmful'],expected)
    self.assertEqual(r.immediate_choice,'harmful')
    self.assertIsNone(r.chosen)
 def test_baseline_and_channel_use_same_initial_basin(self):
  results=[tipping_aware_information_acquisition([self.channels()[0]],base_friction=.4,network_strength=.9,temperature=.08,future_opportunity_value=.5,current_participation=start) for start in (0.,1.)]
  self.assertEqual(results[0].chosen,'trigger')
  self.assertIsNone(results[1].chosen)
  self.assertGreater(results[0].channel_scores['trigger'],0)
  self.assertLess(results[1].channel_scores['trigger'],0)
  self.assertEqual(results[0].equilibria,results[1].equilibria)
if __name__=='__main__': unittest.main()
