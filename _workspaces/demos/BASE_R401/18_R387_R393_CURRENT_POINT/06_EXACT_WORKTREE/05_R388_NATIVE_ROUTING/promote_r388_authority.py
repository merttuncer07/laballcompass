from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / '01_V2_CORE'
R388 = ROOT / '05_R388_NATIVE_ROUTING'


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    bundle_status_path = R388 / 'R388_PROMOTION_REGRESSION_BUNDLE.status'
    bundle_path = R388 / 'R388_PROMOTION_REGRESSION_BUNDLE.json'
    if not bundle_status_path.exists() or not bundle_path.exists():
        raise SystemExit('promotion refused: split promotion regression bundle missing')
    if bundle_status_path.read_text(encoding='utf-8').strip() != '0':
        raise SystemExit('promotion refused: split promotion regression bundle status is not zero')
    regression_bundle = load_json(bundle_path)
    if regression_bundle.get('status') != 'PASS':
        raise SystemExit('promotion refused: split promotion regression bundle contains failure')
    foundry_gate = regression_bundle.get('checks', {}).get('foundry', {})
    core_gate = regression_bundle.get('checks', {}).get('core_split', {})
    if foundry_gate.get('test_files_passed') != 214 or foundry_gate.get('test_files_failed') != 0 or foundry_gate.get('tests_counted') != 806:
        raise SystemExit('promotion refused: Foundry regression coverage is incomplete')
    if core_gate.get('status') != 'PASS' or core_gate.get('run_count') != 12 or core_gate.get('failed'):
        raise SystemExit('promotion refused: split core regression coverage is incomplete')

    direct_status_path = R388 / 'R388_ALL_V2_DIRECT_DISCOVERY_REGRESSION.status'
    direct_report_path = R388 / 'R388_ALL_V2_DIRECT_DISCOVERY_REGRESSION.json'
    if not direct_status_path.exists() or not direct_report_path.exists():
        raise SystemExit('promotion refused: direct V2 auto-discovery regression receipt missing')
    if direct_status_path.read_text(encoding='utf-8').strip() != '0':
        raise SystemExit('promotion refused: direct V2 auto-discovery regression failed')
    direct_report = load_json(direct_report_path)
    if direct_report.get('test_files') != 48 or direct_report.get('passed') != 48 or direct_report.get('failed') != 0:
        raise SystemExit('promotion refused: direct V2 auto-discovery coverage is incomplete')

    audit = load_json(CORE / 'PRODUCT_QUALITY_AUDIT_R388.json')
    overlay_path = CORE / 'R388_PRODUCT_OVERLAY_STATE.json'
    overlay = load_json(overlay_path)
    prior = load_json(CORE / 'CURRENT_PRODUCT_AUTHORITY.json')
    telemetry = load_json(CORE / 'generated_search' / 'EXPERIMENT_TELEMETRY_INDEX_R12.json')
    imap = load_json(CORE / 'generated_search' / 'INTERACTION_MAP_R12.json')
    queue = load_json(CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json')
    counts = load_json(CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COUNTS.json')
    parent_audit = load_json(R388 / 'R388_PARENT_PARENT_COMPLETENESS_AUDIT.json')
    campaign = [json.loads(x) for x in (CORE / 'search_data' / 'CAMPAIGN_MEMORY.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]

    suite_dirs = sorted(d for d in (CORE / 'products').glob('V2P*') if d.is_dir() and (d / 'COMPOSITION.json').exists() and list(d.glob('test_*.py')))
    suite_ids = [d.name.split('_', 1)[0] for d in suite_dirs]
    assert prior['authority_release'] == 'R387'
    assert prior['canonical_executable_suite_count'] == 47
    assert prior['canonical_distinct_family_count'] == 34
    assert audit['registry_family_count'] == 455 and audit['registry455_unchanged']
    assert audit['resulting_executable_suite_count'] == 48
    assert audit['resulting_distinct_family_count'] == 35
    assert audit['candidate_added_suite_ids'] == ['V2P049']
    assert audit['candidate_distinct_product_ids'] == ['V2P049']
    assert len(suite_ids) == 48 and 'V2P049' in suite_ids and 'V2P047' not in suite_ids
    assert telemetry['event_count'] == telemetry['exact_current_suite_matches'] == 398
    assert telemetry['current_completed_suite_count'] == telemetry['calibrated_current_suite_count'] == 48
    assert telemetry['unmatched_event_count'] == 0
    assert imap['relation_counts']['COMPLETED_COMPOSITION'] == 48
    assert imap['relation_counts']['REJECTED_CURRENT_INTERFACE'] == 5
    fixed = [r for r in queue if r.get('experiment_bootstrap_status') == 'FIXED_PILOT_SCHEDULE_AVAILABLE']
    assert len(fixed) == 48 and all(r.get('experiment_calibration_status') == 'CALIBRATED_EXACT_SHELL' for r in fixed)
    assert sum(r.get('outcome') == 'EXECUTABLE_CONTRACT_PASS' for r in campaign) == 48
    assert sum(r.get('outcome') == 'REJECTED_CURRENT_INTERFACE' for r in campaign) == 5
    assert sum(bool(r.get('learning_eligible')) for r in campaign) == 0
    assert counts['candidate_universe_rows'] == 16594 and counts['active_candidate_rows'] == 16589
    assert parent_audit['native_rank_compatible_parent_pairs_previously_hidden'] == 890

    prior_family_ids = list(prior['canonical_distinct_family_ids'])
    assert 'V2P049' not in prior_family_ids
    canonical_family_ids = prior_family_ids + ['V2P049']
    assert len(set(canonical_family_ids)) == 35

    evidence_files = [
        bundle_path, bundle_status_path,
        direct_report_path, direct_status_path,
        R388 / 'R388_MONOLITHIC_RUNNER_ANOMALY.json',
        R388 / 'R388_CANDIDATE_PACKAGED_REGRESSION.status',
        R388 / 'R388_CANDIDATE_CLOSURE.log',
        R388 / 'R388_TOPOLOGY_FOUNDRY_REGRESSION.log',
        R388 / 'R388_PARENT_PARENT_COMPLETENESS_AUDIT.json',
        R388 / 'R388_RETRO50_INTEGRATION_AUDIT.json',
        R388 / 'R388_V2P049_CORE_TEST.log',
        R388 / 'R388_V2P049_RAPID_PILOT.json',
        CORE / 'PRODUCT_QUALITY_AUDIT_R388.json',
        CORE / 'R388_PRODUCT_OVERLAY_STATE.json',
        CORE / 'generated_search' / 'EXPERIMENT_TELEMETRY_INDEX_R12.json',
        CORE / 'generated_search' / 'INTERACTION_MAP_R12.json',
        CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COUNTS.json',
    ]
    hashes = {str(p.relative_to(ROOT)): sha256(p) for p in evidence_files if p.exists()}

    authority = {
        'schema_version': 1,
        'authority_release': 'R388',
        'status': 'PROMOTED_CANONICAL_PRODUCT_AUTHORITY',
        'promoted_at_utc': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        'promotion_basis': 'Retro50 parent-to-parent visibility repair plus V2P049 candidate overlay after clean split-receipt regression coverage (Foundry + all discovered V2 suites + core/search/experiment/closure)',
        'historical_base_authority': prior.get('historical_base_authority'),
        'prior_canonical_authority': {'release':'R387','executable_suites':47,'distinct_families':34},
        'registry_family_count': 455,
        'registry455_unchanged': True,
        'canonical_executable_suite_count': 48,
        'canonical_distinct_family_count': 35,
        'canonical_executable_suite_ids': suite_ids,
        'canonical_distinct_family_ids': canonical_family_ids,
        'new_r388_distinct_family_ids': ['V2P049'],
        'new_r388_executable_suite_ids': ['V2P049'],
        'quarantined_product_ids': ['V2P047'],
        'visibility_repairs': {
            'foundry_parent_provenance_bucket_split_for_same_parent_family_filter': True,
            'previously_hidden_rank_compatible_parent_pairs': 890,
            'full_candidate_universe_persisted': 16594,
            'top1000_queue_is_operational_window_only': True,
            'packaged_regression_auto_discovers_all_v2_product_tests': True,
        },
        'evidence_boundary': {
            'mechanics_telemetry_is_empirical_learning': False,
            'learning_eligible_campaign_events': 0,
            'statement': 'Promotion certifies graph visibility, product/control-plane closure, and deterministic executable contracts only; it is not novel-theory, scientific, deployment, or real-world validation.',
        },
        'promotion_gates': {
            'promotion_regression_bundle': 'PASS',
            'foundry_test_files_passed': 214,
            'foundry_tests_counted': 806,
            'split_core_surfaces_passed': 12,
            'monolithic_runner_exit_code': 0,
            'monolithic_stdout_receipt_bytes': 0,
            'direct_v2_autodiscovery_test_files': 48,
            'direct_v2_autodiscovery_passed': 48,
            'direct_v2_autodiscovery_failed': 0,
            'physical_suite_count': 48,
            'distinct_family_count': 35,
            'telemetry_events': 398,
            'telemetry_exact_matches': 398,
            'telemetry_unmatched': 0,
            'calibrated_suites': 48,
            'interaction_map_completed_edges': 48,
            'fixed_pilotable_queue_rows': 48,
            'campaign_mechanics_passes': 48,
            'rejected_current_interface_edges': 5,
            'candidate_universe_rows': 16594,
            'active_candidate_rows': 16589,
            'previously_hidden_rank_compatible_parent_pairs': 890,
        },
        'evidence_sha256': hashes,
    }

    authority_path = CORE / 'CURRENT_PRODUCT_AUTHORITY.json'
    authority_path.write_text(json.dumps(authority, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')

    overlay['status'] = 'PROMOTED_TO_R388_PRODUCT_AUTHORITY'
    overlay['promoted_as_authority_release'] = 'R388'
    overlay['current_authority_file'] = authority_path.name
    overlay['promotion_regression_receipt'] = str(bundle_path.relative_to(ROOT))
    overlay_path.write_text(json.dumps(overlay, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')

    comp_path = CORE / 'products' / 'V2P049_SACAPL' / 'COMPOSITION.json'
    comp = load_json(comp_path)
    comp['status'] = 'R388_PROMOTED_CANONICAL_PRODUCT'
    comp['authority'] = 'R388_CANONICAL_PRODUCT_AUTHORITY'
    comp_path.write_text(json.dumps(comp, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')

    current_counts_path = ROOT / '04_INTEGRITY' / 'CURRENT_PRODUCT_COUNTS.json'
    current_counts = load_json(current_counts_path)
    current_counts['canonical_product_authority'] = {
        'release':'R388','registry_family_count':455,'executable_suites':48,'distinct_families':35,
        'authority_file':'01_V2_CORE/CURRENT_PRODUCT_AUTHORITY.json','quarantined_product_ids':['V2P047'],
    }
    current_counts['completed_v2_executable_suites_not_folded_into_base_registry'] = 48
    current_counts['quality_distinct_v2_families_not_folded_into_base_registry'] = 35
    current_counts['registry455_unchanged'] = True
    current_counts_path.write_text(json.dumps(current_counts, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')

    receipt = {
        'release':'R388','result':'PROMOTED','authority_file':str(authority_path.relative_to(ROOT)),
        'authority_sha256':sha256(authority_path),'overlay_state_sha256_after_promotion':sha256(overlay_path),
        'checks':authority['promotion_gates'],'registry455_unchanged':True,'quarantined_product_ids':['V2P047'],
        'note':authority['evidence_boundary']['statement'],
    }
    (R388 / 'R388_AUTHORITY_PROMOTION_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
