import unittest, numpy as np
from pcfdlw import closure_fidelity_decision_selection as f

def data():
 y=np.array([[1.,0.],[0.,1.],[1.,0.],[0.,1.]])
 unsafe_train=y.copy()
 safe_train=y.copy(); safe_train[0]=[.4,.6]
 unsafe_val=1-y
 safe_val=y.copy()
 tr={'unsafe':unsafe_train,'safe':safe_train}; va={'unsafe':unsafe_val,'safe':safe_val}
 return tr,y,va,y
class T(unittest.TestCase):
 def calc(self,cv=None,pi=None):
  tr,y,va,z=data(); return f(tr,y,va,z,[[1,0],[0,1]],initial_action_exposure=[.5,.5],closure_violation=cv or {'unsafe':.3,'safe':.01},predictive_improvement=pi or {'unsafe':.2,'safe':.1},allowed_closure_rate=.1,min_predictive_improvement=.05)
 def test_blind_prefers_unsafe(self): self.assertEqual(self.calc().blind_selected,'unsafe')
 def test_guarded_selects_safe(self): self.assertEqual(self.calc().selected,'safe')
 def test_rejection_visible(self): self.assertIn('unsafe',self.calc().rejected_candidates)
 def test_all_certified_matches_blind(self): self.assertEqual(self.calc(cv={'unsafe':0,'safe':0}).selected,self.calc(cv={'unsafe':0,'safe':0}).blind_selected)
 def test_no_certified_abstains(self): self.assertIsNone(self.calc(cv={'unsafe':.2,'safe':.2}).selected)
 def test_fidelity_floor_applies(self): self.assertIsNone(self.calc(cv={'unsafe':0,'safe':0},pi={'unsafe':0,'safe':0}).selected)
 def test_key_mismatch(self):
  tr,y,va,z=data()
  with self.assertRaises(ValueError): f(tr,y,va,z,[[1,0],[0,1]],initial_action_exposure=[.5,.5],closure_violation={'unsafe':0},predictive_improvement={'unsafe':1},allowed_closure_rate=.1,min_predictive_improvement=0)
 def test_guard_improves_holdout_regret_in_construction(self):
  r=self.calc(); self.assertLess(r.guarded_validation_regret,r.blind_validation_regret)
 def test_status(self): self.assertIn('CLOSURE_FIDELITY',self.calc().status)
if __name__=='__main__': unittest.main()
