from __future__ import annotations

import csv, json, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
CORE = LAB / '01_V2_CORE'
sys.path.insert(0, str(CORE))

from core_v2 import CapabilityProfile, rank_composition
from build_core_v2_foundry import evidence_weight
from experiment_contract_bootstrap import discover_existing_composition_suites

REG = CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl'
PARENTS = CORE / 'generated' / 'FOUNDRY_PARENT_INTERFACE_REGISTRY.json'
ADJ = CORE / 'COMPOSITION_EDGE_ADJUDICATIONS.jsonl'
CARRIED = HERE / 'R386_CARRIED_STATIC_DISPOSITIONS.jsonl'


def load_jsonl(path: Path):
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def main():
    rows = load_jsonl(REG)
    by_id = {r['capability_id']: r for r in rows}
    profiles = {
        r['capability_id']: CapabilityProfile(
            r['capability_id'], r['name'], r['family'], r['evidence_tier'],
            frozenset(r['strength_tags']), frozenset(r['weakness_tags']),
            frozenset(r['input_types']), frozenset(r['output_types']),
            r['standalone_value'], r['component_value'])
        for r in rows
    }
    parent_rows = json.loads(PARENTS.read_text(encoding='utf-8'))
    retro_ids = {
        'PARENT:' + r['product_dir']
        for r in parent_rows
        if 'RETRO_PRODUCTS' in str(r.get('relative_path', ''))
    }
    current_parent_ids = {
        'PARENT:' + r['product_dir']
        for r in parent_rows
        if 'RETRO_PRODUCTS' not in str(r.get('relative_path', ''))
    }
    assert len(retro_ids) == 50
    assert len(current_parent_ids) == 19
    assert retro_ids | current_parent_ids == {r['capability_id'] for r in rows if r['family'] == 'FOUNDRY_PARENT'}

    prior = {(r['supplier_id'], r['consumer_id']): r for r in load_jsonl(CARRIED)}
    adjudications = {(r['supplier_id'], r['consumer_id']): r for r in load_jsonl(ADJ)}
    suites = discover_existing_composition_suites(CORE)

    candidates = []
    for supplier in profiles.values():
        for consumer in profiles.values():
            if supplier.capability_id == consumer.capability_id:
                continue
            if supplier.capability_id not in retro_ids and consumer.capability_id not in retro_ids:
                continue
            # R388 reservoir rule: the Retro50 may be paired with every other native capability,
            # including FOUNDRY_PARENT peers that the legacy structural-family guard excluded.
            c = rank_composition(
                supplier, consumer,
                evidence_weight=evidence_weight(supplier.evidence_tier) + evidence_weight(consumer.evidence_tier),
            )
            if c is None:
                continue
            pair = (c.supplier_id, c.consumer_id)
            sr, cr = by_id[c.supplier_id], by_id[c.consumer_id]
            legacy_eligible = (
                sr['family'] != cr['family']
                and ('FOUNDRY' in sr['family'] or 'FOUNDRY' in cr['family'])
            )
            same_parent_expansion = sr['family'] == cr['family'] == 'FOUNDRY_PARENT'
            old = prior.get(pair)
            adj = adjudications.get(pair)
            suite = suites.get(pair)
            row = {
                'supplier_id': c.supplier_id,
                'consumer_id': c.consumer_id,
                'supplier_name': supplier.name,
                'consumer_name': consumer.name,
                'supplier_family': sr['family'],
                'consumer_family': cr['family'],
                'score': c.score,
                'interface_matches': list(c.interface_matches),
                'addressed_weaknesses': list(c.addressed_weaknesses),
                'shared_domains': list(c.shared_domains),
                'supplier_is_retro50': c.supplier_id in retro_ids,
                'consumer_is_retro50': c.consumer_id in retro_ids,
                'legacy_policy_eligible': legacy_eligible,
                'new_same_parent_family_expansion': same_parent_expansion,
                'candidate_origin': 'R388_RETRO50_SAME_PARENT_EXPANSION' if same_parent_expansion else 'R388_RETRO50_EXISTING_NATIVE_SPACE',
                'r386_disposition': old.get('disposition') if old else None,
                'r386_rationale': old.get('rationale') if old else None,
                'r386_raw_native_rank': old.get('raw_native_rank') if old else None,
                'current_adjudication_state': adj.get('state') if adj else None,
                'current_adjudication_reason': (adj.get('adjudication_reason') or adj.get('reason')) if adj else None,
                'completed_product_id': suite.product_id if suite else None,
                'needs_fresh_adjudication': old is None and adj is None and suite is None,
            }
            candidates.append(row)

    candidates.sort(key=lambda r: (-r['score'], r['supplier_id'], r['consumer_id']))
    for i, r in enumerate(candidates, 1): r['retro_native_rank'] = i

    all_jsonl = HERE / 'R388_RETRO50_NATIVE_CANDIDATES.jsonl'
    all_jsonl.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in candidates), encoding='utf-8')
    new_rows = [r for r in candidates if r['new_same_parent_family_expansion']]
    (HERE / 'R388_RETRO50_NEW_PARENT_FAMILY_CANDIDATES.jsonl').write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in new_rows), encoding='utf-8')
    fresh = [r for r in candidates if r['needs_fresh_adjudication']]
    (HERE / 'R388_RETRO50_FRESH_ADJUDICATION_QUEUE.jsonl').write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in fresh), encoding='utf-8')

    fields = [
        'retro_native_rank','supplier_id','consumer_id','supplier_name','consumer_name','supplier_family','consumer_family',
        'score','supplier_is_retro50','consumer_is_retro50','legacy_policy_eligible','new_same_parent_family_expansion',
        'candidate_origin','r386_disposition','r386_raw_native_rank','current_adjudication_state','completed_product_id',
        'needs_fresh_adjudication','interface_matches','addressed_weaknesses','shared_domains'
    ]
    with (HERE / 'R388_RETRO50_NATIVE_CANDIDATES.tsv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fields, delimiter='\t', extrasaction='ignore'); w.writeheader()
        for r in candidates:
            out = dict(r)
            for k in ('interface_matches','addressed_weaknesses','shared_domains'): out[k] = ','.join(out[k])
            w.writerow(out)

    audit = {
        'release': 'R388_SHADOW_RETRO50_NATIVE_INTEGRATION',
        'authority_status': 'SHADOW_ONLY_NO_PRODUCT_PROMOTION',
        'registry_record_count_unchanged': len(rows),
        'retro50_record_count': len(retro_ids),
        'current_nonretro_parent_count': len(current_parent_ids),
        'candidate_count_involving_retro50': len(candidates),
        'legacy_policy_eligible_candidate_count': sum(r['legacy_policy_eligible'] for r in candidates),
        'new_same_parent_family_candidate_count': len(new_rows),
        'retro_to_retro_candidate_count': sum(r['supplier_is_retro50'] and r['consumer_is_retro50'] for r in new_rows),
        'retro_to_current_parent_candidate_count': sum(r['supplier_is_retro50'] and r['consumer_id'] in current_parent_ids for r in new_rows),
        'current_parent_to_retro_candidate_count': sum(r['supplier_id'] in current_parent_ids and r['consumer_is_retro50'] for r in new_rows),
        'carried_r386_disposition_count': sum(r['r386_disposition'] is not None for r in candidates),
        'current_adjudication_count': sum(r['current_adjudication_state'] is not None for r in candidates),
        'completed_suite_pair_count': sum(r['completed_product_id'] is not None for r in candidates),
        'fresh_adjudication_count': len(fresh),
        'fresh_same_parent_family_count': sum(r['needs_fresh_adjudication'] and r['new_same_parent_family_expansion'] for r in candidates),
        'fresh_existing_native_space_count': sum(r['needs_fresh_adjudication'] and not r['new_same_parent_family_expansion'] for r in candidates),
        'candidate_origin_counts': dict(Counter(r['candidate_origin'] for r in candidates)),
        'counterpart_family_counts': dict(Counter(
            r['consumer_family'] if r['supplier_is_retro50'] else r['supplier_family'] for r in candidates
        )),
        'nonclaims': [
            'candidate generation is not product-family promotion',
            'R386 static collapse labels are carried as triage provenance, not certified equivalence',
            'Retro50 standalone products remain a separate reservoir and do not increment Quality34 automatically',
        ],
    }
    (HERE / 'R388_RETRO50_INTEGRATION_AUDIT.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(audit, indent=2))
    print('top fresh')
    for r in fresh[:20]:
        print(r['retro_native_rank'], r['supplier_id'], '->', r['consumer_id'], r['score'], r['candidate_origin'], r['interface_matches'], r['addressed_weaknesses'])

if __name__ == '__main__': main()
