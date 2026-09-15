from __future__ import annotations
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
class R392Closure(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.audit=load(ROOT/'PRODUCT_QUALITY_AUDIT_R392.json'); cls.overlay=load(ROOT/'R392_PRODUCT_OVERLAY_STATE.json'); cls.auth=load(ROOT/'CURRENT_PRODUCT_AUTHORITY.json')
  cls.tel=load(ROOT/'generated_search/EXPERIMENT_TELEMETRY_INDEX_R12.json'); cls.imap=load(ROOT/'generated_search/INTERACTION_MAP_R12.json'); cls.queue=load(ROOT/'generated_v2_foundry/CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'); cls.counts=load(ROOT/'generated_v2_foundry/CORE_V2_FOUNDRY_COUNTS.json'); cls.state=load(ROOT/'generated_search/LAB_STATE_R12.json')
  cls.products={d.name.split('_',1)[0] for d in (ROOT/'products').glob('V2P*') if d.is_dir() and (d/'COMPOSITION.json').exists() and list(d.glob('test_*.py'))}
 def test_candidate_counts_and_quarantine(self):
  self.assertGreaterEqual(len(self.products),52); self.assertEqual(self.audit['resulting_executable_suite_count'],52); self.assertEqual(self.audit['resulting_distinct_family_count'],39); self.assertIn('V2P053',self.products); self.assertNotIn('V2P047',self.products)
 def test_authority_transition_is_explicit(self):
  self.assertGreaterEqual(int(self.auth['authority_release'][1:]),391)
  if self.auth['authority_release']=='R391':
   self.assertEqual(self.auth['canonical_executable_suite_count'],51); self.assertEqual(self.auth['canonical_distinct_family_count'],38); self.assertEqual(self.overlay['status'],'CANDIDATE_OVERLAY_PENDING_R392_PROMOTION')
  elif self.auth['authority_release']=='R392':
   self.assertEqual(self.auth['canonical_executable_suite_count'],52); self.assertEqual(self.auth['canonical_distinct_family_count'],39); self.assertEqual(self.overlay['status'],'PROMOTED_TO_R392_PRODUCT_AUTHORITY')
  else:
   self.assertGreaterEqual(self.auth['canonical_executable_suite_count'],52); self.assertGreaterEqual(self.auth['canonical_distinct_family_count'],39); self.assertEqual(self.overlay['status'],'PROMOTED_TO_R392_PRODUCT_AUTHORITY')
 def test_v2p053_exact_shell(self):
  row=next(r for r in self.queue if (r['supplier_id'],r['consumer_id'])==('FOUNDRY:P090','PARENT:R041_CONSTRAINED_POLICY_CAPL'))
  self.assertEqual(row['experiment_bootstrap_product_id'],'V2P053'); self.assertEqual(row['experiment_bootstrap_case_count'],12); self.assertEqual(row['experiment_telemetry_event_count'],12); self.assertEqual(row['experiment_calibration_status'],'CALIBRATED_EXACT_SHELL')
 def test_control_plane_closes_over_52(self):
  self.assertEqual(self.tel['event_count'],447); self.assertEqual(self.tel['current_completed_suite_count'],52); self.assertEqual(self.tel['calibrated_current_suite_count'],52); self.assertEqual(self.tel['exact_current_suite_matches'],447); self.assertEqual(self.tel['unmatched_event_count'],0); self.assertEqual(self.imap['relation_counts']['COMPLETED_COMPOSITION'],52); self.assertEqual(self.imap['relation_counts']['REJECTED_CURRENT_INTERFACE'],5)
 def test_state_overlay_separate_from_authority(self):
  pq=self.state['product_quality']; self.assertEqual(pq['candidate_overlay']['audit'],'PRODUCT_QUALITY_AUDIT_R392.json'); self.assertEqual(pq['candidate_overlay']['executable_suites'],52); self.assertEqual(pq['candidate_overlay']['distinct_families'],39); self.assertTrue(pq['observed_matches_candidate_overlay']); self.assertEqual(pq['canonical_product_authority']['authority_release'],self.auth['authority_release'])
 def test_visibility_inherited(self):
  self.assertEqual(self.counts['candidate_universe_rows'],16594); self.assertEqual(self.state['candidate_universe']['persistence'],'FULL_RANKED_UNIVERSE'); self.assertEqual(self.state['queue']['role'],'TOP_1000_OPERATIONAL_PRIORITY_WINDOW'); self.assertGreater(self.counts['candidate_universe_rows'],self.counts['queue_rows'])
 def test_mechanics_nonlearning(self):
  rows=[json.loads(x) for x in (ROOT/'search_data/CAMPAIGN_MEMORY.jsonl').read_text().splitlines() if x.strip()]; self.assertEqual(sum(r.get('outcome')=='EXECUTABLE_CONTRACT_PASS' for r in rows),52); self.assertEqual(sum(r.get('outcome')=='REJECTED_CURRENT_INTERFACE' for r in rows),5); self.assertEqual(sum(bool(r.get('learning_eligible')) for r in rows),0)
 def test_quality_controls_present(self):
  r=self.audit['rows'][0]; self.assertEqual(r['product_id'],'V2P053'); self.assertTrue(r['new_failure_mode']); self.assertTrue(r['non_additive_interaction']); self.assertTrue(r['mechanism_removing_comparator']); self.assertGreaterEqual(len(r['nearest_existing_products']),4); self.assertEqual(r['test_methods'],12); self.assertIn('conditional',r['sensitivity_boundary'])
 def test_registry455_unchanged(self): self.assertTrue(self.audit['registry455_unchanged']); self.assertEqual(self.audit['registry_family_count'],455); self.assertTrue(self.auth['registry455_unchanged']); self.assertEqual(self.auth['registry_family_count'],455)
 def test_full_visibility_not_top1000_only(self): self.assertEqual(self.counts['candidate_universe_rows'],16594); self.assertEqual(self.counts['queue_rows'],1000)
if __name__=='__main__': unittest.main()
