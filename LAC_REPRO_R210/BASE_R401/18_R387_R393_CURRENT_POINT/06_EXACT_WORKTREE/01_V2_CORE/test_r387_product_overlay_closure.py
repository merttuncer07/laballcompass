from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


class R387ProductOverlayClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load('PRODUCT_QUALITY_AUDIT_R386.json')
        cls.overlay = load('R386_PRODUCT_OVERLAY_STATE.json')
        cls.telemetry = load('generated_search/EXPERIMENT_TELEMETRY_INDEX_R12.json')
        cls.imap = load('generated_search/INTERACTION_MAP_R12.json')
        cls.queue = load('generated_v2_foundry/CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json')
        cls.state = load('generated_search/LAB_STATE_R12.json')
        cls.products = {
            d.name.split('_', 1)[0]
            for d in (ROOT / 'products').glob('V2P*')
            if (d / 'COMPOSITION.json').exists() and list(d.glob('test_*.py'))
        }

    def test_registry_authority_is_not_inflated(self):
        self.assertEqual(self.audit['registry_family_count'], 455)
        self.assertTrue(self.overlay['registry455_unchanged'])
        self.assertEqual(self.state['product_quality']['canonical_product_authority']['registry_family_count'], 455)

    def test_r386_overlay_history_remains_intact(self):
        self.assertEqual(self.audit['resulting_executable_suite_count'], 47)
        self.assertEqual(self.overlay['candidate_counts']['products_executable_suites'], 47)
        self.assertTrue(set(self.audit['promoted_product_ids']).issubset(self.products))
        self.assertGreaterEqual(len(self.products), 47)

    def test_quality_family_accounting_is_distinct_from_suite_count(self):
        self.assertEqual(self.audit['resulting_distinct_family_count'], 34)
        self.assertEqual(self.overlay['candidate_counts']['quality_distinct_families'], 34)
        self.assertEqual(len(self.audit['distinct_product_ids']), 6)
        self.assertEqual(self.audit['r386_executable_family_variants'], 3)

    def test_promoted_and_quarantined_ids_are_disjoint_and_complete(self):
        promoted = set(self.audit['promoted_product_ids'])
        quarantined = set(self.audit['quarantined_product_ids'])
        self.assertEqual(len(promoted), 9)
        self.assertEqual(promoted, set(self.overlay['promoted_native_suite_ids']))
        self.assertEqual(quarantined, {'V2P047'})
        self.assertTrue(promoted.issubset(self.products))
        self.assertTrue(quarantined.isdisjoint(self.products))

    def test_current_control_plane_contains_the_r387_suite_set(self):
        current = self.telemetry['current_completed_suite_count']
        self.assertEqual(current, len(self.products))
        self.assertEqual(self.telemetry['calibrated_current_suite_count'], current)
        self.assertEqual(self.telemetry['exact_current_suite_matches'], self.telemetry['event_count'])
        self.assertEqual(self.telemetry['unmatched_event_count'], 0)
        self.assertEqual(self.imap['relation_counts']['COMPLETED_COMPOSITION'], current)
        known = [r for r in self.queue if r.get('experiment_bootstrap_status') == 'FIXED_PILOT_SCHEDULE_AVAILABLE']
        self.assertEqual(len(known), current)
        self.assertTrue(all(r.get('experiment_calibration_status') == 'CALIBRATED_EXACT_SHELL' for r in known))
        self.assertTrue(set(self.audit['promoted_product_ids']).issubset({r.get('experiment_bootstrap_product_id') for r in known}))

    def test_mechanics_telemetry_is_not_empirical_learning(self):
        rows = [json.loads(x) for x in (ROOT / 'search_data' / 'CAMPAIGN_MEMORY.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        self.assertEqual(sum(r['outcome'] == 'EXECUTABLE_CONTRACT_PASS' for r in rows), len(self.products))
        rejected_count = len(load('generated_v2_foundry/CORE_V2_FOUNDRY_REJECTED_EDGES.json'))
        self.assertEqual(sum(r['outcome'] == 'REJECTED_CURRENT_INTERFACE' for r in rows), rejected_count)
        self.assertGreaterEqual(rejected_count, 4)
        self.assertEqual(sum(bool(r['learning_eligible']) for r in rows), 0)

    def test_state_keeps_r387_authority_separate_from_later_candidate_overlays(self):
        pq = self.state['product_quality']
        self.assertEqual(pq['base_authority']['executable_suites'], 38)
        self.assertEqual(pq['base_authority']['distinct_families'], 28)
        authority_state = load('CURRENT_PRODUCT_AUTHORITY.json')
        self.assertGreaterEqual(int(authority_state['authority_release'][1:]), 387)
        self.assertEqual(authority_state['status'], 'PROMOTED_CANONICAL_PRODUCT_AUTHORITY')
        self.assertTrue(authority_state['registry455_unchanged'])
        self.assertEqual(authority_state['quarantined_product_ids'], ['V2P047'])
        if authority_state['authority_release'] == 'R387':
            self.assertEqual(authority_state['canonical_executable_suite_count'], 47)
            self.assertEqual(authority_state['canonical_distinct_family_count'], 34)
        else:
            self.assertGreaterEqual(authority_state['canonical_executable_suite_count'], 47)
            self.assertGreaterEqual(authority_state['canonical_distinct_family_count'], 34)
        # Historical R386 accounting is immutable even when LAB_STATE points at a newer overlay.
        self.assertEqual(self.audit['resulting_executable_suite_count'], 47)
        self.assertEqual(self.audit['resulting_distinct_family_count'], 34)



if __name__ == '__main__':
    unittest.main()
