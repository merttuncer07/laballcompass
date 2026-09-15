import unittest, numpy as np, importlib.util, pathlib, sys
from cdtdlew import *
PACKAGE_ROOT=pathlib.Path(__file__).resolve().parents[3]
P=PACKAGE_ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R044_DECISION_LOSS_DLEW/dlew.py'
s=importlib.util.spec_from_file_location('dlew_r386',P); dlew=importlib.util.module_from_spec(s); sys.modules['dlew_r386']=dlew; s.loader.exec_module(dlew)
def case():
 rng=np.random.default_rng(0)
 def outcome(n):
  common=.001+rng.normal(scale=.002,size=n); spread=rng.normal(scale=.012,size=n); return np.c_[common+spread,common-spread]
 yt=outcome(500); yv=outcome(1000)
 def preds(y,q,salt):
  rr=np.random.default_rng(int(q*1000)+salt); stable=y+rr.normal(scale=.008,size=y.shape)
  if q<=.8: fragile=y+rr.normal(scale=.003,size=y.shape)
  else:
   common=y.mean(1,keepdims=True); spread=(y[:,0]-y[:,1])[:,None]/2; a=min(1,(q-.8)/.1); ps=(1-2*a)*spread
   fragile=np.c_[common[:,0]+ps[:,0],common[:,0]-ps[:,0]]+rr.normal(scale=.002,size=y.shape)
  return {'stable':stable,'fragile':fragile}
 rp={q:(preds(yt,q,1),preds(yv,q,2)) for q in (.7,.8,.9)}
 return channel_tipping_robust_selection(dlew.evaluate_decision_models,yt,yv,rp,[[1,0],[0,1]],baseline_channel={'parameter':.7,'decision':True},dominance_records=[{'parameter':.7,'decision':True},{'parameter':.8,'decision':True},{'parameter':.9,'decision':False}],initial_action_exposure=[.5,.5],evaluation_channel=.9)
class T(unittest.TestCase):
 def test_tipping_found(self): self.assertAlmostEqual(case()['tipping_parameter'],.9)
 def test_baseline_is_fragile(self): self.assertEqual(case()['baseline_selected'],'fragile')
 def test_robust_selects_stable(self): self.assertEqual(case()['selected'],'stable')
 def test_gain_positive(self): self.assertGreater(case()['gain_vs_removed_mechanism'],0)
 def test_protected_interval(self): self.assertEqual(case()['protected_regimes'],[.7,.8,.9])
 def test_worst_case_exposes_fragility(self): self.assertGreater(case()['worst_case_training_regret']['fragile'],case()['worst_case_training_regret']['stable'])
 def test_no_flip_helper(self): self.assertIsNone(dominance_tipping([{'parameter':.8,'decision':1}],{'parameter':.7,'decision':1}))
 def test_empty_protected_rejected(self):
  with self.assertRaises(ValueError): channel_tipping_robust_selection(None,np.zeros((2,2)),np.zeros((2,2)),{},[[1,0],[0,1]],baseline_channel={'parameter':.7,'decision':1},dominance_records=[],initial_action_exposure=[.5,.5])
if __name__=='__main__': unittest.main()
