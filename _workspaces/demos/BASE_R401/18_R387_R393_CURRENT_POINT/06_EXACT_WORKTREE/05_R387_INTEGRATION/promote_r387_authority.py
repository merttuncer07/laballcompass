from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / '01_V2_CORE'
INTEGRATION = ROOT / '05_R387_INTEGRATION'


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    regression_status = (INTEGRATION / 'R387_PACKAGED_REGRESSION_FINAL.status').read_text(encoding='utf-8').strip()
    regression = load_json(INTEGRATION / 'R387_PACKAGED_REGRESSION_FINAL.log')
    if regression_status != '0' or regression.get('status') != 'PASS':
        raise SystemExit('promotion refused: packaged regression is not clean')
    failed = [r.get('label') for r in regression.get('runs', []) if r.get('exit_code') != 0]
    if failed:
        raise SystemExit(f'promotion refused: failed packaged regression runs: {failed}')

    audit = load_json(CORE / 'PRODUCT_QUALITY_AUDIT_R386.json')
    overlay_path = CORE / 'R386_PRODUCT_OVERLAY_STATE.json'
    overlay = load_json(overlay_path)
    telemetry = load_json(CORE / 'generated_search' / 'EXPERIMENT_TELEMETRY_INDEX_R12.json')
    imap = load_json(CORE / 'generated_search' / 'INTERACTION_MAP_R12.json')
    queue = load_json(CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json')
    campaign_rows = [
        json.loads(line)
        for line in (CORE / 'search_data' / 'CAMPAIGN_MEMORY.jsonl').read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]

    suite_dirs = sorted(
        d for d in (CORE / 'products').glob('V2P*')
        if d.is_dir() and (d / 'COMPOSITION.json').exists() and list(d.glob('test_*.py'))
    )
    suite_ids = [d.name.split('_', 1)[0] for d in suite_dirs]

    assert audit['registry_family_count'] == 455
    assert audit['resulting_executable_suite_count'] == 47
    assert audit['resulting_distinct_family_count'] == 34
    assert len(suite_ids) == 47
    assert 'V2P047' not in suite_ids
    assert set(audit['quarantined_product_ids']) == {'V2P047'}
    assert set(audit['promoted_product_ids']).issubset(set(suite_ids))

    assert telemetry['current_completed_suite_count'] == 47
    assert telemetry['calibrated_current_suite_count'] == 47
    assert telemetry['exact_current_suite_matches'] == telemetry['event_count'] == 388
    assert telemetry['unmatched_event_count'] == 0
    assert imap['relation_counts']['COMPLETED_COMPOSITION'] == 47
    fixed = [r for r in queue if r.get('experiment_bootstrap_status') == 'FIXED_PILOT_SCHEDULE_AVAILABLE']
    assert len(fixed) == 47
    assert all(r.get('experiment_calibration_status') == 'CALIBRATED_EXACT_SHELL' for r in fixed)
    assert sum(r.get('outcome') == 'EXECUTABLE_CONTRACT_PASS' for r in campaign_rows) == 47
    assert sum(r.get('outcome') == 'REJECTED_CURRENT_INTERFACE' for r in campaign_rows) == 4
    assert sum(bool(r.get('learning_eligible')) for r in campaign_rows) == 0

    base_audit = load_json(CORE / 'PRODUCT_QUALITY_AUDIT_V1.json')
    base_family_ids = sorted({r['family_id'] for r in base_audit['rows'] if r.get('family_id')})
    new_distinct = list(audit['distinct_product_ids'])
    canonical_family_ids = base_family_ids + new_distinct
    assert len(base_family_ids) == 28
    assert len(set(canonical_family_ids)) == 34

    evidence_files = [
        INTEGRATION / 'R387_PACKAGED_REGRESSION_FINAL.log',
        INTEGRATION / 'R387_PACKAGED_REGRESSION_FINAL.status',
        INTEGRATION / 'R387_PRODUCT_OVERLAY_CLOSURE.log',
        INTEGRATION / 'R387_EXPERIMENT_INTEGRATION.log',
        INTEGRATION / 'R387_TELEMETRY_REBUILD.status',
        CORE / 'PRODUCT_QUALITY_AUDIT_R386.json',
        CORE / 'R386_PRODUCT_OVERLAY_STATE.json',
        CORE / 'generated_search' / 'EXPERIMENT_TELEMETRY_INDEX_R12.json',
        CORE / 'generated_search' / 'INTERACTION_MAP_R12.json',
    ]
    hashes = {str(p.relative_to(ROOT)): sha256(p) for p in evidence_files if p.exists()}

    authority = {
        'schema_version': 1,
        'authority_release': 'R387',
        'status': 'PROMOTED_CANONICAL_PRODUCT_AUTHORITY',
        'promoted_at_utc': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        'promotion_basis': 'R386 candidate product overlay after R387 portability repair and clean full packaged regression',
        'historical_base_authority': {
            'release': 'R12',
            'registry_family_count': 455,
            'executable_suites': 38,
            'distinct_families': 28,
            'audit': 'PRODUCT_QUALITY_AUDIT_V1.json',
        },
        'registry_family_count': 455,
        'registry455_unchanged': True,
        'canonical_executable_suite_count': 47,
        'canonical_distinct_family_count': 34,
        'canonical_executable_suite_ids': suite_ids,
        'canonical_distinct_family_ids': canonical_family_ids,
        'new_r386_distinct_family_ids': new_distinct,
        'r386_executable_family_variant_ids': list(audit['variant_product_ids']),
        'r386_promoted_native_suite_ids': list(audit['promoted_product_ids']),
        'quarantined_product_ids': ['V2P047'],
        'evidence_boundary': {
            'mechanics_telemetry_is_empirical_learning': False,
            'learning_eligible_campaign_events': 0,
            'statement': 'Promotion certifies product/control-plane closure and deterministic executable contracts only; it is not scientific, deployment, or real-world validation.',
        },
        'promotion_gates': {
            'packaged_regression': 'PASS',
            'packaged_regression_exit_code': 0,
            'physical_suite_count': 47,
            'distinct_family_count': 34,
            'telemetry_events': 388,
            'telemetry_exact_matches': 388,
            'telemetry_unmatched': 0,
            'calibrated_suites': 47,
            'interaction_map_completed_edges': 47,
            'fixed_pilotable_queue_rows': 47,
            'campaign_mechanics_passes': 47,
            'rejected_current_interface_edges': 4,
        },
        'evidence_sha256': hashes,
    }

    authority_path = CORE / 'CURRENT_PRODUCT_AUTHORITY.json'
    authority_path.write_text(json.dumps(authority, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')

    # R386 source audit remains unchanged; only the mutable overlay-state marker records the transition.
    overlay['status'] = 'PROMOTED_TO_R387_PRODUCT_AUTHORITY'
    overlay['promoted_as_authority_release'] = 'R387'
    overlay['current_authority_file'] = authority_path.name
    overlay['promotion_regression_receipt'] = str((INTEGRATION / 'R387_PACKAGED_REGRESSION_FINAL.log').relative_to(ROOT))
    overlay_path.write_text(json.dumps(overlay, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')

    current_counts = load_json(ROOT / '04_INTEGRITY' / 'CURRENT_PRODUCT_COUNTS.json')
    current_counts['canonical_product_authority'] = {
        'release': 'R387',
        'registry_family_count': 455,
        'executable_suites': 47,
        'distinct_families': 34,
        'authority_file': '01_V2_CORE/CURRENT_PRODUCT_AUTHORITY.json',
        'quarantined_product_ids': ['V2P047'],
    }
    current_counts['completed_v2_executable_suites_not_folded_into_base_registry'] = 47
    current_counts['quality_distinct_v2_families_not_folded_into_base_registry'] = 34
    current_counts['registry455_unchanged'] = True
    (ROOT / '04_INTEGRITY' / 'CURRENT_PRODUCT_COUNTS.json').write_text(
        json.dumps(current_counts, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8'
    )

    receipt = {
        'release': 'R387',
        'result': 'PROMOTED',
        'authority_file': str(authority_path.relative_to(ROOT)),
        'authority_sha256': sha256(authority_path),
        'overlay_state_sha256_after_promotion': sha256(overlay_path),
        'checks': authority['promotion_gates'],
        'registry455_unchanged': True,
        'quarantined_product_ids': ['V2P047'],
        'note': authority['evidence_boundary']['statement'],
    }
    (INTEGRATION / 'R387_AUTHORITY_PROMOTION_RECEIPT.json').write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8'
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
