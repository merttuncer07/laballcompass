from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
R388 = LAB / '05_R388_NATIVE_ROUTING'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


class R388Retro50ParentIntegrationClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load(ROOT / 'PRODUCT_QUALITY_AUDIT_R388.json')
        cls.overlay = load(ROOT / 'R388_PRODUCT_OVERLAY_STATE.json')
        cls.authority = load(ROOT / 'CURRENT_PRODUCT_AUTHORITY.json')
        cls.telemetry = load(ROOT / 'generated_search' / 'EXPERIMENT_TELEMETRY_INDEX_R12.json')
        cls.imap = load(ROOT / 'generated_search' / 'INTERACTION_MAP_R12.json')
        cls.queue = load(ROOT / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json')
        cls.counts = load(ROOT / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COUNTS.json')
        cls.state = load(ROOT / 'generated_search' / 'LAB_STATE_R12.json')
        cls.parent_audit = load(R388 / 'R388_PARENT_PARENT_COMPLETENESS_AUDIT.json')
        cls.products = {
            d.name.split('_', 1)[0]
            for d in (ROOT / 'products').glob('V2P*')
            if d.is_dir() and (d / 'COMPOSITION.json').exists() and list(d.glob('test_*.py'))
        }

    def test_parent_provenance_bucket_no_longer_hides_parent_pairs(self):
        self.assertEqual(self.parent_audit['parent_record_count'], 69)
        self.assertEqual(self.parent_audit['retro_parent_count'], 50)
        self.assertEqual(self.parent_audit['current_parent_count'], 19)
        self.assertEqual(self.parent_audit['native_rank_compatible_parent_pairs_previously_hidden'], 890)
        self.assertEqual(self.parent_audit['breakdown']['RETRO_TO_RETRO'], 422)
        self.assertEqual(self.parent_audit['breakdown']['RETRO_TO_CURRENT_PARENT'], 250)
        self.assertEqual(self.parent_audit['breakdown']['CURRENT_PARENT_TO_RETRO'], 140)
        self.assertEqual(self.parent_audit['breakdown']['CURRENT_PARENT_TO_CURRENT_PARENT'], 78)

    def test_full_candidate_universe_is_preserved_beyond_operational_top1000(self):
        self.assertEqual(self.counts['candidate_universe_rows'], 16594)
        self.assertEqual(self.counts['active_candidate_rows'], 16589)
        self.assertEqual(self.counts['queue_rows'], 1000)
        self.assertGreater(self.counts['candidate_universe_rows'], self.counts['queue_rows'])
        self.assertEqual(self.state['candidate_universe']['persistence'], 'FULL_RANKED_UNIVERSE')
        self.assertEqual(self.state['queue']['role'], 'TOP_1000_OPERATIONAL_PRIORITY_WINDOW')

    def test_candidate_overlay_is_48_suites_35_internal_families_without_registry_mutation(self):
        self.assertGreaterEqual(len(self.products), 48)
        self.assertTrue(set(self.audit['physical_candidate_suite_ids']).issubset(self.products))
        self.assertEqual(self.audit['resulting_executable_suite_count'], 48)
        self.assertEqual(self.audit['resulting_distinct_family_count'], 35)
        self.assertEqual(self.audit['candidate_added_suite_ids'], ['V2P049'])
        self.assertEqual(self.audit['candidate_distinct_product_ids'], ['V2P049'])
        self.assertEqual(self.audit['registry_family_count'], 455)
        self.assertTrue(self.audit['registry455_unchanged'])
        self.assertNotIn('V2P047', self.products)
        self.assertIn('V2P049', self.products)
        # A later materialized overlay may be the live observed state; R388 remains immutable history.
        if self.state['product_quality']['candidate_overlay']['audit'] == 'PRODUCT_QUALITY_AUDIT_R388.json':
            self.assertTrue(self.state['product_quality']['observed_matches_candidate_overlay'])
        else:
            self.assertGreaterEqual(self.state['product_quality']['observed_executable_suites'], 48)

    def test_v2p049_is_exactly_calibrated(self):
        pair = ('PARENT:R037_SUPPORT_COVARIANCE_SACPS', 'PARENT:R041_CONSTRAINED_POLICY_CAPL')
        row = next(r for r in self.queue if (r['supplier_id'], r['consumer_id']) == pair)
        self.assertEqual(row['experiment_bootstrap_product_id'], 'V2P049')
        self.assertEqual(row['experiment_bootstrap_case_count'], 10)
        self.assertEqual(row['experiment_calibration_status'], 'CALIBRATED_EXACT_SHELL')
        self.assertEqual(row['experiment_telemetry_event_count'], 10)

    def test_control_plane_closes_over_48_candidate_suites(self):
        current = self.telemetry['current_completed_suite_count']
        self.assertGreaterEqual(current, 48)
        self.assertEqual(self.telemetry['calibrated_current_suite_count'], current)
        self.assertGreaterEqual(self.telemetry['event_count'], 398)
        self.assertEqual(self.telemetry['exact_current_suite_matches'], self.telemetry['event_count'])
        self.assertEqual(self.telemetry['unmatched_event_count'], 0)
        self.assertEqual(self.imap['relation_counts']['COMPLETED_COMPOSITION'], current)
        self.assertEqual(self.imap['relation_counts']['REJECTED_CURRENT_INTERFACE'], 5)
        fixed = [r for r in self.queue if r.get('experiment_bootstrap_status') == 'FIXED_PILOT_SCHEDULE_AVAILABLE']
        self.assertEqual(len(fixed), current)

    def test_mechanics_events_remain_nonlearning(self):
        rows = [json.loads(x) for x in (ROOT / 'search_data' / 'CAMPAIGN_MEMORY.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        self.assertEqual(sum(r.get('outcome') == 'EXECUTABLE_CONTRACT_PASS' for r in rows), len(self.products))
        self.assertEqual(sum(r.get('outcome') == 'REJECTED_CURRENT_INTERFACE' for r in rows), 5)
        self.assertEqual(sum(bool(r.get('learning_eligible')) for r in rows), 0)

    def test_authority_transition_is_explicit_not_inferred_from_candidate_state(self):
        self.assertGreaterEqual(int(self.authority['authority_release'][1:]), 387)
        if self.authority['authority_release'] == 'R387':
            self.assertEqual(self.authority['canonical_executable_suite_count'], 47)
            self.assertEqual(self.authority['canonical_distinct_family_count'], 34)
        elif self.authority['authority_release'] == 'R388':
            self.assertEqual(self.authority['canonical_executable_suite_count'], 48)
            self.assertEqual(self.authority['canonical_distinct_family_count'], 35)
        else:
            self.assertGreaterEqual(self.authority['canonical_executable_suite_count'], 48)
            self.assertGreaterEqual(self.authority['canonical_distinct_family_count'], 35)
        self.assertEqual(self.overlay['status'], 'PROMOTED_TO_R388_PRODUCT_AUTHORITY')
        self.assertEqual(self.authority['quarantined_product_ids'], ['V2P047'])
        self.assertTrue(self.authority['registry455_unchanged'])


if __name__ == '__main__':
    unittest.main()
