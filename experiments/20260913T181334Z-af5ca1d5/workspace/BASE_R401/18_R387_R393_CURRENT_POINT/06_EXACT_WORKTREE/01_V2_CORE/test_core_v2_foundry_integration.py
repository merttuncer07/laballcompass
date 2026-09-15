from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path


ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'products'/'V2P001_SAVA'))
from sava import AuditCandidate,allocate_verification_liquidity
sys.path.insert(0,str(ROOT/'products'/'V2P002_MFQA'))
from mfqa import FidelityChannel,allocate_quasineutral_measurements


class FoundryIntegrationTests(unittest.TestCase):
    def test_unified_registry_has_all_three_families(self):
        path=ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl'
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(rows),310)
        self.assertEqual({r['family'] for r in rows},{'LCB_KERNEL','FOUNDRY_PARENT','FOUNDRY_PRODUCT'})

    def test_foundry_evidence_tiers_remain_distinct(self):
        rows=[json.loads(line) for line in (ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl').read_text(encoding='utf-8').splitlines()]
        tiers={r['evidence_tier'] for r in rows if r['family']=='FOUNDRY_PRODUCT'}
        self.assertIn('ORIGINAL_EXECUTABLE_MATERIAL',tiers)
        self.assertIn('SPEC_EXECUTABLE_FROM_RESULTS',tiers)
        self.assertIn('NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID',tiers)

    def test_curated_evlt_route_is_in_queue(self):
        with (ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.tsv').open(encoding='utf-8') as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        row=next(r for r in rows if r['supplier_id']=='LCB-K003' and r['consumer_id']=='FOUNDRY:P031')
        self.assertEqual(row['curated'],'True')

    def test_sava_removes_shared_capacity_double_count(self):
        cs=[AuditCandidate('A',1.,(60,0)),AuditCandidate('B',1.,(60,40)),AuditCandidate('C',1.,(0,40))]
        r=allocate_verification_liquidity(cs,(60,40),[(.7,set()),(.25,{'A'}),(.05,{'B'})])
        self.assertGreater(r.overlap_removed_value,0)
        self.assertEqual(sum(r.allocated_shared_capacity.values()),100)

    def test_mfqa_routes_by_decision_value_and_correlation(self):
        fine=FidelityChannel('fine',.0025,.002)
        cheap=FidelityChannel('cheap',.025,.0002)
        common=dict(
            belief_variance=.01,tolerance=.05,total_budget=.1,
            fine_channel=fine,cheap_channel=cheap,min_fine=4,min_correlation=.2,
        )
        high=allocate_quasineutral_measurements(.052,pilot_correlation=.92,**common)
        low=allocate_quasineutral_measurements(.052,pilot_correlation=.05,**common)
        far=allocate_quasineutral_measurements(.35,pilot_correlation=.92,**common)
        self.assertEqual((high.mode,low.mode,far.mode),('multifidelity','fine_only','no_measurement'))
        self.assertLess(high.variance_proxy,low.variance_proxy)
        self.assertEqual(far.spent_budget,0)

    def test_rejected_k058_p143_edge_is_preserved_in_adjudication_not_active_queue(self):
        rows=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        self.assertFalse(any(r['supplier_id']=='LCB-K058' and r['consumer_id']=='FOUNDRY:P143' for r in rows))
        rejected=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_REJECTED_EDGES.json').read_text(encoding='utf-8'))
        row=next(r for r in rejected if r['supplier_id']=='LCB-K058' and r['consumer_id']=='FOUNDRY:P143')
        self.assertEqual(row['adjudication_state'],'REJECTED_CURRENT_INTERFACE')
        self.assertFalse(row['active_for_build'])
        self.assertIn('constrained LP',row['adjudication_reason'])
        self.assertIn('unconstrained binary QUBO',row['adjudication_reason'])

    def test_edsanp_edge_is_now_fixed_pilot_ready(self):
        rows=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        row=next(r for r in rows if r['supplier_id']=='LCB-K019' and r['consumer_id']=='FOUNDRY:P003')
        self.assertEqual(row['experiment_bootstrap_status'],'FIXED_PILOT_SCHEDULE_AVAILABLE')
        self.assertEqual(row['experiment_bootstrap_product_id'],'V2P005')
        self.assertEqual(row['experiment_bootstrap_case_count'],12)



    def test_r10_k089_edges_are_rejected_without_global_component_death(self):
        rows=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        rejected=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_REJECTED_EDGES.json').read_text(encoding='utf-8'))
        for consumer in ('FOUNDRY:P137','FOUNDRY:P142'):
            self.assertFalse(any(r['supplier_id']=='LCB-K089' and r['consumer_id']==consumer for r in rows))
            row=next(r for r in rejected if r['supplier_id']=='LCB-K089' and r['consumer_id']==consumer)
            self.assertEqual(row['adjudication_state'],'REJECTED_CURRENT_INTERFACE')
            self.assertFalse(row['active_for_build'])

    def test_r10_k068_p025_is_fixed_pilot_ready_v2p006(self):
        rows=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        row=next(r for r in rows if r['supplier_id']=='LCB-K068' and r['consumer_id']=='FOUNDRY:P025')
        self.assertEqual(row['experiment_bootstrap_status'],'FIXED_PILOT_SCHEDULE_AVAILABLE')
        self.assertEqual(row['experiment_bootstrap_product_id'],'V2P006')
        self.assertEqual(row['experiment_bootstrap_case_count'],12)

    def test_r11_k087_p002_is_rejected_without_component_death(self):
        rows=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        rejected=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_REJECTED_EDGES.json').read_text(encoding='utf-8'))
        self.assertFalse(any(r['supplier_id']=='LCB-K087' and r['consumer_id']=='FOUNDRY:P002' for r in rows))
        row=next(r for r in rejected if r['supplier_id']=='LCB-K087' and r['consumer_id']=='FOUNDRY:P002')
        self.assertEqual(row['adjudication_state'],'REJECTED_CURRENT_INTERFACE')
        self.assertIn('scalar score',row['adjudication_reason'])
        self.assertIn('transition closure',row['adjudication_reason'])

    def test_r11_k009_p026_is_fixed_pilot_ready_v2p007(self):
        rows=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        row=next(r for r in rows if r['supplier_id']=='LCB-K009' and r['consumer_id']=='FOUNDRY:P026')
        self.assertEqual(row['experiment_bootstrap_status'],'FIXED_PILOT_SCHEDULE_AVAILABLE')
        self.assertEqual(row['experiment_bootstrap_product_id'],'V2P007')
        self.assertEqual(row['experiment_bootstrap_case_count'],12)

    def test_r388_parent_provenance_bucket_does_not_hide_parent_to_parent_edges(self):
        rows=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        pairs={(r['supplier_id'],r['consumer_id']) for r in rows}
        # Current-parent -> current-parent was impossible under the legacy generic-family guard.
        self.assertIn(('PARENT:IM334_IM094_DRE','PARENT:IM359_IM014_AICC'),pairs)
        # Retro -> current-parent verifies that the historical executable reservoir is equally visible.
        self.assertIn(('PARENT:R037_SUPPORT_COVARIANCE_SACPS','PARENT:IM334_IM094_DRE'),pairs)

    def test_r388_parent_completeness_audit_accounts_for_all_previously_hidden_rankable_pairs(self):
        audit=json.loads((ROOT.parent/'05_R388_NATIVE_ROUTING'/'R388_PARENT_PARENT_COMPLETENESS_AUDIT.json').read_text(encoding='utf-8'))
        self.assertEqual(audit['parent_record_count'],69)
        self.assertEqual(audit['directed_parent_pairs_before_compatibility'],4692)
        self.assertEqual(audit['native_rank_compatible_parent_pairs_previously_hidden'],890)
        self.assertEqual(sum(audit['breakdown'].values()),890)

    def test_r388_full_candidate_universe_is_persisted_beyond_top1000_priority_window(self):
        counts=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COUNTS.json').read_text(encoding='utf-8'))
        universe=[json.loads(x) for x in (ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        queue=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        self.assertEqual(len(universe),counts['candidate_edges'])
        self.assertGreater(len(universe),len(queue))
        self.assertEqual(len(queue),1000)
        self.assertEqual(sum(bool(r.get('active_for_build',True)) for r in universe),counts['active_candidate_rows'])

    def test_r388_operational_queue_pins_every_completed_suite(self):
        counts=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COUNTS.json').read_text(encoding='utf-8'))
        queue=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
        completed=[r for r in queue if r.get('experiment_bootstrap_status')=='FIXED_PILOT_SCHEDULE_AVAILABLE']
        self.assertEqual(len(completed),counts['calibrated_completed_suites'])
        self.assertEqual(counts['queue_completed_suite_rows'],counts['calibrated_completed_suites'])
        self.assertTrue(any(r.get('active_candidate_rank',0)>1000 for r in completed))

    def test_r388_interaction_map_represents_full_active_candidate_universe(self):
        counts=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COUNTS.json').read_text(encoding='utf-8'))
        imap=json.loads((ROOT/'generated_search'/'INTERACTION_MAP_R12.json').read_text(encoding='utf-8'))
        represented=imap['relation_counts'].get('COMPLETED_COMPOSITION',0)+imap['relation_counts'].get('CURATED_HYPOTHESIS',0)+imap['relation_counts'].get('INFERRED_CANDIDATE',0)
        self.assertEqual(represented,counts['active_candidate_rows'])

if __name__=='__main__':unittest.main()
