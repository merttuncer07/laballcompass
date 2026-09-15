import importlib.util,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]/'LAC_REPRO_R210'

def load(name):
 p=next(p for p in ROOT.rglob(name+'.py') if 'parent_products' in str(p)) if name not in ('symbolic_favorable','spec_runtime') else next(ROOT.rglob(name+'.py'))
 spec=importlib.util.spec_from_file_location('restored_'+name,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
class EngineRepairs(unittest.TestCase):
 def test_sacps_test_data_does_not_select_model(self):
  m=load('sacps');rng=np.random.default_rng(42);train=rng.multivariate_normal([0,0],[[1,.8],[.8,1]],40)
  h1=rng.multivariate_normal([0,0],[[1,.95],[.95,1]],300);h2=rng.multivariate_normal([0,0],[[1,-.9],[-.9,1]],300)
  a=m.estimate_support_aware_covariance(train,np.ones((2,2)),holdout_returns=h1);b=m.estimate_support_aware_covariance(train,np.ones((2,2)),holdout_returns=h2)
  self.assertEqual(a.selected_shrinkage,b.selected_shrinkage);np.testing.assert_array_equal(a.covariance,b.covariance)
 def test_sacps_explicit_validation_separate(self):
  m=load('sacps');rng=np.random.default_rng(4);train=rng.normal(size=(20,3));cal=rng.normal(size=(15,3));test=rng.normal(size=(12,3))
  a=m.estimate_support_aware_covariance(train,np.eye(3),validation_returns=cal,holdout_returns=test)
  self.assertIsNotNone(a.realized_holdout_variance)
 def test_rel_rejects_nan_evidence(self):
  m=load('rel')
  with self.assertRaises(ValueError):m.EvidenceRecord('a','party',float('nan'))
 def test_rel_duplicate_relation_ids_rejected(self):
  m=load('rel');rs=[m.EvidenceRecord('a','a',1),m.EvidenceRecord('b','b',2)]
  with self.assertRaises(ValueError):m.RelationalEvidenceLocalizer().localize(rs,[m.ConsistencyRelation('r','a','b'),m.ConsistencyRelation('r','a','b')])
 def test_rel_empty_inputs_explained(self):
  m=load('rel')
  with self.assertRaisesRegex(ValueError,'record'):m.RelationalEvidenceLocalizer().localize([],[])
 def test_aicc_degenerate_observation(self):
  m=load('aicc');c=m.InformationChannel('zero',np.array([1.]),0,0);ctl=m.AdaptiveInformationController(np.array([2.]),np.zeros((1,1)),np.array([[1.],[-1.]]),np.zeros(2),[c]);ctl.update(c,2.)
  np.testing.assert_array_equal(ctl.mean,[2.]);self.assertTrue(np.isfinite(ctl.covariance).all())
  with self.assertRaises(ValueError):ctl.update(c,3.)
 def test_aicc_rejects_non_psd_belief(self):
  m=load('aicc')
  with self.assertRaises(ValueError):m.AdaptiveInformationController(np.zeros(2),np.array([[1,2],[2,1]]),np.ones((1,2)),np.zeros(1),[])
 def test_aicc_rejects_negative_noise(self):
  m=load('aicc')
  with self.assertRaises(ValueError):m.InformationChannel('bad',np.ones(1),-1)
 def test_csid_nan_coverage_rejected(self):
  m=load('csid')
  with self.assertRaises(ValueError):m.Safeguard('a',1,'f',{'loss':float('nan')})
 def test_csid_duplicate_failure_ids_rejected(self):
  m=load('csid')
  with self.assertRaises(ValueError):m.ContractSafeguardDesigner([m.FailureMode('loss',.1,100),m.FailureMode('loss',.2,100)],[])
 def test_hfad_self_loop_has_zero_boundary(self):
  m=load('hfad');b=m.incidence_from_edges(1,[(0,0)]);np.testing.assert_array_equal(b,np.zeros((1,1)));r=m.HodgeFlowAttributionDecomposer(b).decompose(np.array([7.]));self.assertAlmostEqual(r.harmonic_energy,49)
 def test_hfad_empty_edges(self):
  m=load('hfad');r=m.HodgeFlowAttributionDecomposer(np.zeros((2,0))).decompose(np.empty(0));self.assertEqual(r.reconstruction_residual,0)
 def test_maslov_missing_head_rejected(self):
  m=load('symbolic_favorable')
  with self.assertRaises(ValueError):m.compile_circuit_acyclic([m.Rule('b',('a',)),m.Rule('goal',('b',))],{'a':'source'},['b'])
 def test_maslov_deep_proof(self):
  m=load('symbolic_favorable');c=m.MonotoneCircuit();n=c.variable('s');enabled={'s'}
  for i in range(1500):
   v=c.variable(i);enabled.add(i);n=c.combine('and' if i%2 else 'or',[n,v])
  self.assertTrue(c.evaluate(n,enabled))
 def test_spec_audit_requires_protected_measurement(self):
  m=load('spec_runtime');spec={'product_id':'x','short_name':'x','execution_mode':'audit'}
  with self.assertRaises(ValueError):m.evaluate_spec_product(spec,[{'name':'a','selection_score':4}])
 def test_spec_negative_cost_rejected(self):
  m=load('spec_runtime');spec={'product_id':'x','short_name':'x','execution_mode':'allocation'}
  with self.assertRaises(ValueError):m.evaluate_spec_product(spec,[{'name':'a','cost':-3,'value':10}],budget=0)
if __name__=='__main__':unittest.main()

class CompositionRepairs(unittest.TestCase):
 def shared(self):
  p=next(ROOT.rglob('shared_foundry.py'));spec=importlib.util.spec_from_file_location('shared_repair',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_transport_invariant_to_row_order(self):
  m=self.shared();a=m.mawt([0,10],[1,1],[10,0],[1,1]);self.assertAlmostEqual(a['normalized_w2'],0)
 def test_transport_zero_mass_not_nan(self):
  m=self.shared();a=m.mawt([0],[0],[1],[2]);self.assertIsNone(a['normalized_w2']);self.assertEqual(a['created_mass'],2)
 def test_plain_transfer_not_circulation(self):
  m=self.shared();a=m.cacf([('A','B',10),('B','C',10)],{'A','B','C'});self.assertAlmostEqual(a['circulation_energy'],0,places=10)
 def test_circulation_row_order_invariant(self):
  m=self.shared();e=[('A','B',10),('B','C',10),('C','A',10)];a=m.cacf(e,{'A','B','C'});b=m.cacf(e[::-1],{'A','B','C'});self.assertAlmostEqual(a['circulation_energy'],300);self.assertAlmostEqual(a['circulation_energy'],b['circulation_energy'])
 def test_frontier_matches_exhaustive_oracle(self):
  from itertools import combinations
  import random
  m=load('spec_runtime');spec={'product_id':'x','short_name':'x','execution_mode':'allocation'};rng=random.Random(13)
  for n in range(1,9):
   rows=[{'name':str(i),'cost':rng.randrange(0,6),'value':rng.randrange(-3,10)} for i in range(n)]
   expected=max((sum(r['value'] for r in chosen),-sum(r['cost'] for r in chosen)) for k in range(n+1) for chosen in combinations(rows,k) if sum(r['cost'] for r in chosen)<=7)
   actual=m.evaluate_spec_product(spec,rows,budget=7);self.assertEqual((actual['total_value'],-actual['total_cost']),expected)
 def test_large_frontier_allocation(self):
  m=load('spec_runtime');spec={'product_id':'x','short_name':'x','execution_mode':'allocation'};r=m.evaluate_spec_product(spec,[{'name':str(i),'cost':1,'value':i} for i in range(100)],budget=10);self.assertEqual(r['total_value'],sum(range(90,100)))
