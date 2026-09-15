import importlib.util,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]/'LAC_REPRO_R210'
sys.path.insert(0,str(ROOT))
import lab_kernels as k

def recovered(name):
 p=next(ROOT.rglob(name+'.py'));spec=importlib.util.spec_from_file_location('probe_'+name,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
class KernelRecoveryRepairs(unittest.TestCase):
 def test_all_kernel_exports_are_accessible(self):self.assertEqual(len(k.__all__),91)
 def test_zero_sensor_budget_has_rank_zero(self):
  r=k.ObservabilityCoveragePlannerV0.select([[1.,0.],[0.,1.]],0);self.assertEqual(r['rank'],0);self.assertEqual(r['selected_indices'],[])
 def test_fractional_sensor_budget_rejected(self):
  with self.assertRaises(ValueError):k.ObservabilityCoveragePlannerV0.select([[1]],.5)
 def test_shared_capacity_rejects_negative_rewards(self):
  with self.assertRaises(ValueError):k.SharedCapacityAllocatorV0(lambda s:len(s)).allocate([1,-1])
 def test_recovered_observability_selects_independent_directions(self):
  r=recovered('v2p057_reoc').select([1,1],[[10,0],[9,0],[0,1]],2);self.assertEqual(r.sensors,(0,2))
 def test_robust_merge_rejects_indefinite_covariance(self):
  with self.assertRaises(ValueError):recovered('v2p056_sacrdsbc').robust_merge([.5,.5],[.55,.45],[[1,2],[2,1]],.1)
 def test_single_coordinate_recovery_covariance_is_matrix(self):
  c=recovered('v2p056_sacrdsbc').support_covariance([[1],[2],[3]],[[1]]);self.assertEqual(c.shape,(1,1))
 def test_single_coordinate_memory(self):
  e=recovered('v2p058_sacatrc').choose_eviction([.1,.2],[[1],[2]],[[1]],.2);self.assertIn(e.index,e.safe_set)
 def test_empty_recovered_allocation_explained(self):
  with self.assertRaises(ValueError):recovered('v2p054_cadsbc').removal_control([],0)
if __name__=='__main__':unittest.main()
