import unittest
from bivcp import boundary_information_capacity_plan

def base(prior=(0.55,0.45), cost=0.4):
    return dict(states=['low','high'],prior=prior,actions=['lean','reserve'],action_capacity={'lean':5,'reserve':10},action_cost={'lean':0,'reserve':2.5},demand={'low':5,'high':10},shortfall_penalty=2.0,channels={'probe':{'cost':cost,'likelihood':{'L':{'low':0.9,'high':0.1},'H':{'low':0.1,'high':0.9}}}})

class T(unittest.TestCase):
 def test_near_boundary_acquires(self): self.assertTrue(boundary_information_capacity_plan(**base()).acquired)
 def test_acquisition_reduces_total_expected_loss(self):
  r=boundary_information_capacity_plan(**base()); self.assertLess(r.expected_total_loss,r.baseline_loss)
 def test_channel_named(self): self.assertEqual(boundary_information_capacity_plan(**base()).channel,'probe')
 def test_far_prior_skips(self): self.assertFalse(boundary_information_capacity_plan(**base(prior=(0.99,0.01))).acquired)
 def test_expensive_channel_skips(self): self.assertFalse(boundary_information_capacity_plan(**base(cost=10)).acquired)
 def test_cost_cap_skips(self): self.assertFalse(boundary_information_capacity_plan(**base(),max_channel_cost=0.1).acquired)
 def test_probabilities_normalized(self):
  a=base(prior=(55,45)); b=base(prior=(.55,.45)); self.assertAlmostEqual(boundary_information_capacity_plan(**a).baseline_loss,boundary_information_capacity_plan(**b).baseline_loss)
 def test_zero_mass_rejected(self):
  k=base(prior=(0,0));
  with self.assertRaises(ValueError): boundary_information_capacity_plan(**k)
 def test_empty_actions_rejected(self):
  k=base(); k['actions']=[]
  with self.assertRaises(ValueError): boundary_information_capacity_plan(**k)
 def test_information_value_positive_when_acquired(self): self.assertGreater(boundary_information_capacity_plan(**base()).information_value,0)
 def test_mechanism_removing_comparator_is_baseline(self):
  r=boundary_information_capacity_plan(**base()); self.assertGreater(r.baseline_loss,r.expected_total_loss)
 def test_status(self): self.assertEqual(boundary_information_capacity_plan(**base()).status,'BOUNDARY_INFORMATION_ACQUIRED_BEFORE_CAPACITY_COMMITMENT')
if __name__=='__main__': unittest.main()
