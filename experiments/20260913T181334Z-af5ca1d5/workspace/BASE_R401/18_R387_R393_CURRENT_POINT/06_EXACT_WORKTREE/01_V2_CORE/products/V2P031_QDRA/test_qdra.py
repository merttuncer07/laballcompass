import unittest
from qdra import *
from qdra import ResolutionOption
class T(unittest.TestCase):
 def opts(self): return [ResolutionOption('coarse',1,.5,.5),ResolutionOption('fine',3,.05,.05)]
 def regs(self): return [ValidityRegion('near',.049,.0004,.05,5),ValidityRegion('far',.005,.000025,.05,20)]
 def test_near_gets_more_weight(self):
  r=quasineutral_decision_resolution(self.regs(),self.opts(),budget=4); self.assertGreater(r.decision_weights['near'],r.decision_weights['far'])
 def test_budget_respected(self): self.assertLessEqual(quasineutral_decision_resolution(self.regs(),self.opts(),budget=4).allocation['total_cost'],4+1e-9)
 def test_all_regions_allocated(self): self.assertEqual(len(quasineutral_decision_resolution(self.regs(),self.opts(),budget=4).allocation['allocations']),2)
 def test_far_from_boundary_weight_small(self): self.assertLess(quasineutral_decision_resolution(self.regs(),self.opts(),budget=4).decision_weights['far'],1)
 def test_zero_variance_far_weight_zero(self): self.assertEqual(quasineutral_decision_resolution([ValidityRegion('x',0,0,1,1)],self.opts(),budget=1).decision_weights['x'],0)
 def test_empty_rejected(self):
  with self.assertRaises(ValueError): quasineutral_decision_resolution([],self.opts(),budget=1)
 def test_status(self): self.assertIn('BOUNDARY',quasineutral_decision_resolution(self.regs(),self.opts(),budget=4).status)
 def test_fine_selected_near_when_budget_allows(self):
  r=quasineutral_decision_resolution(self.regs(),self.opts(),budget=4); a={x['region']:x['option'] for x in r.allocation['allocations']}; self.assertEqual(a['near'],'fine')
if __name__=='__main__': unittest.main()
