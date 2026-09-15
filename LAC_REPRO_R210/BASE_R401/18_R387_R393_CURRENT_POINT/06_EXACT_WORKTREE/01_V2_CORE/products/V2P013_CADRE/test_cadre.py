import unittest
from cadre import GaussianArm, compression_aware_dre

def arm(n,m,v=.04): return GaussianArm(n,m,v,.2,0)
def near():
 return [arm('A',1.00),arm('B',.98),arm('C',.2,1.0)]
def full():
 return [arm('A',.96),arm('B',1.03),arm('C',.2,1.0)]
class T(unittest.TestCase):
 def test_near_margin_uncertified(self): self.assertFalse(compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':.05,'B':.05,'C':0},remaining_decisions=10).compression_certified)
 def test_uncertified_without_full_abstains(self): self.assertIsNone(compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':.05,'B':.05,'C':0},remaining_decisions=10).final_choice)
 def test_full_resolution_used(self): self.assertTrue(compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':.05,'B':.05,'C':0},remaining_decisions=10,full_resolution_arms=full()).used_full_resolution)
 def test_full_resolution_repairs_choice(self):
  r=compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':.05,'B':.05,'C':0},remaining_decisions=10,full_resolution_arms=full()); self.assertNotEqual(r.compressed_choice,r.final_choice)
 def test_small_bounds_certify(self): self.assertTrue(compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':1e-6,'B':1e-6,'C':0},remaining_decisions=10).compression_certified)
 def test_certified_does_not_use_full(self): self.assertFalse(compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':1e-6,'B':1e-6,'C':0},remaining_decisions=10,full_resolution_arms=full()).used_full_resolution)
 def test_negative_bound_rejected(self):
  with self.assertRaises(ValueError): compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':-.1,'B':0,'C':0},remaining_decisions=10)
 def test_key_mismatch_rejected(self):
  with self.assertRaises(ValueError): compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':0,'B':0},remaining_decisions=10)
 def test_full_name_mismatch_rejected(self):
  with self.assertRaises(ValueError): compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':.1,'B':.1,'C':0},remaining_decisions=10,full_resolution_arms=[arm('A',1),arm('X',1),arm('C',0)])
 def test_two_arms_required(self):
  with self.assertRaises(ValueError): compression_aware_dre(compressed_arms=[arm('A',1)],compression_error_bounds={'A':0},remaining_decisions=10)
 def test_bound_is_top_two_sum(self):
  r=compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':.05,'B':.05,'C':0},remaining_decisions=10); self.assertAlmostEqual(r.compression_decision_bound,.1)
 def test_mechanism_removing_comparator_is_blind_compressed_choice(self):
  r=compression_aware_dre(compressed_arms=near(),compression_error_bounds={'A':.05,'B':.05,'C':0},remaining_decisions=10,full_resolution_arms=full()); self.assertNotEqual(r.compressed_choice,r.final_choice)
if __name__=='__main__': unittest.main()
