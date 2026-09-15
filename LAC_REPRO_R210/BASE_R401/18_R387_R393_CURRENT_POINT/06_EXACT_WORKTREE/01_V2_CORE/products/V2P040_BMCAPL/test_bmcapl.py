import unittest, numpy as np, importlib.util, pathlib, sys
from bmcapl import *
PACKAGE_ROOT=pathlib.Path(__file__).resolve().parents[3]
CAPL=PACKAGE_ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R041_CONSTRAINED_POLICY_CAPL/capl.py'
s=importlib.util.spec_from_file_location('capl_r386',CAPL); capl=importlib.util.module_from_spec(s); sys.modules['capl_r386']=capl; s.loader.exec_module(capl)
def case(seed=0,records=None):
 rng=np.random.default_rng(seed); xt=rng.normal(size=(100,2)); xv=rng.normal(size=(200,2))
 def ret(x,sign,noise):
  pred=np.column_stack((.018*sign*x[:,0],-.018*sign*x[:,0],.014*sign*x[:,1])); return .001+pred+rng.normal(scale=noise,size=pred.shape)
 rt=ret(xt,1,.004); rv=ret(xv,-.35,.008)
 rec=records or [{'parameter':0.50,'decision':True},{'parameter':0.66,'decision':False}]
 return belief_margin_constrained_policy(capl.learn_portfolio_policy,xt,rt,xv,rv,rec,{'parameter':.50,'decision':True},base_turnover=.8,safe_margin=.85,learner_kwargs=dict(maximum_asset_weight=.75,risk_aversion=2.,transaction_cost=.0004,population_size=30,generations=8,seed=3))
class T(unittest.TestCase):
 def test_tipping_shrinks_feasible_turnover(self): self.assertLess(case()['effective_turnover'],.8)
 def test_removal_control_differs(self): self.assertGreater(case()['gain_vs_removed_mechanism'],0)
 def test_candidate_turnover_lower(self): self.assertLess(case()['candidate_average_turnover'],case()['control_average_turnover'])
 def test_constraints_preserved(self): self.assertIn('CERTIFIED',case()['candidate_status'])
 def test_no_flip_reduces_to_control_turnover(self):
  r=case(records=[{'parameter':.5,'decision':True},{'parameter':.8,'decision':True}]); self.assertAlmostEqual(r['effective_turnover'],.8)
 def test_distance(self): self.assertAlmostEqual(tipping_distance([{'parameter':.7,'decision':0}],{'parameter':.5,'decision':1}),.2)
 def test_empty_rejected(self):
  with self.assertRaises(ValueError): tipping_distance([],{'parameter':0,'decision':0})
 def test_bad_margin_rejected(self):
  rng=np.random.default_rng(1); x=rng.normal(size=(5,1)); r=np.c_[rng.normal(size=5),rng.normal(size=5)]
  with self.assertRaises(ValueError): belief_margin_constrained_policy(lambda *a,**k:None,x,r,x,r,[{'parameter':1,'decision':1}],{'parameter':1,'decision':1},base_turnover=.8,safe_margin=0,learner_kwargs={})
if __name__=='__main__': unittest.main()
