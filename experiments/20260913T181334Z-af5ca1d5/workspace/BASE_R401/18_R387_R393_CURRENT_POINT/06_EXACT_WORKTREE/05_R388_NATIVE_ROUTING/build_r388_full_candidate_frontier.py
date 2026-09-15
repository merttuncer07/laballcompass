from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
CORE = LAB / '01_V2_CORE'
UNIVERSE = CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl'
REG = CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl'
PARENTS = CORE / 'generated' / 'FOUNDRY_PARENT_INTERFACE_REGISTRY.json'
ADJ = CORE / 'COMPOSITION_EDGE_ADJUDICATIONS.jsonl'
CARRIED = HERE / 'R386_CARRIED_STATIC_DISPOSITIONS.jsonl'
SHADOW_ROOT = HERE / 'SHADOW_PRODUCTS'


def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def main():
    universe = load_jsonl(UNIVERSE)
    registry = {r['capability_id']: r for r in load_jsonl(REG)}
    carried = {(r['supplier_id'], r['consumer_id']): r for r in load_jsonl(CARRIED)}
    adjudications = {(r['supplier_id'], r['consumer_id']): r for r in load_jsonl(ADJ)}

    parent_rows = json.loads(PARENTS.read_text(encoding='utf-8'))
    parent_kind = {
        'PARENT:' + r['product_dir']: ('RETRO' if 'RETRO_PRODUCTS' in str(r.get('relative_path', '')) else 'CURRENT_PARENT')
        for r in parent_rows
    }

    canonical_authority = json.loads((CORE / 'CURRENT_PRODUCT_AUTHORITY.json').read_text(encoding='utf-8'))
    canonical_ids = set(canonical_authority['canonical_executable_suite_ids'])
    canonical_pairs = {}
    for d in sorted((CORE / 'products').glob('V2P*')):
        comp = d / 'COMPOSITION.json'
        if not comp.exists():
            continue
        o = json.loads(comp.read_text(encoding='utf-8'))
        pid = o.get('product_id') or d.name.split('_', 1)[0]
        if pid in canonical_ids:
            canonical_pairs[(o['supplier_id'], o['consumer_id'])] = pid

    shadow_pairs = {}
    if SHADOW_ROOT.exists():
        for comp in SHADOW_ROOT.glob('V2P*/COMPOSITION.json'):
            o = json.loads(comp.read_text(encoding='utf-8'))
            shadow_pairs[(o['supplier_id'], o['consumer_id'])] = o['product_id']

    def endpoint_kind(cid: str) -> str:
        if cid in parent_kind:
            return parent_kind[cid]
        return registry[cid]['family']

    rows = []
    for r in universe:
        pair = (r['supplier_id'], r['consumer_id'])
        prior = carried.get(pair)
        adj = adjudications.get(pair)
        canonical = canonical_pairs.get(pair)
        shadow = shadow_pairs.get(pair)
        sr, cr = registry[pair[0]], registry[pair[1]]
        parent_parent = sr['family'] == cr['family'] == 'FOUNDRY_PARENT'
        seen_classes = []
        if prior is not None: seen_classes.append('R386_CARRIED_DISPOSITION')
        if adj is not None: seen_classes.append('CURRENT_EXPLICIT_ADJUDICATION')
        if canonical is not None: seen_classes.append('CANONICAL_EXECUTABLE_SUITE')
        if shadow is not None: seen_classes.append('R388_SHADOW_EXECUTABLE_SUITE')
        fresh = not seen_classes
        row = dict(r)
        row.update({
            'supplier_name': sr.get('name', pair[0]),
            'consumer_name': cr.get('name', pair[1]),
            'supplier_kind': endpoint_kind(pair[0]),
            'consumer_kind': endpoint_kind(pair[1]),
            'new_parent_parent_visibility': parent_parent,
            'visibility_origin': 'R388_PREVIOUSLY_HIDDEN_PARENT_PARENT' if parent_parent else 'PREEXISTING_GENERATABLE_NATIVE_UNIVERSE',
            'r386_disposition': prior.get('disposition') if prior else None,
            'r386_rationale': prior.get('rationale') if prior else None,
            'current_adjudication_state': (adj.get('adjudication_state') or adj.get('state')) if adj else None,
            'current_adjudication_reason': (adj.get('reason') or adj.get('adjudication_reason')) if adj else None,
            'canonical_product_id': canonical,
            'shadow_product_id': shadow,
            'already_seen_classes': seen_classes,
            'needs_fresh_adjudication': fresh,
        })
        rows.append(row)

    rows.sort(key=lambda r: int(r.get('candidate_universe_rank') or 10**9))
    fresh = [r for r in rows if r['needs_fresh_adjudication']]

    (HERE / 'R388_FULL_CANDIDATE_FRONTIER.jsonl').write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    (HERE / 'R388_FULL_FRESH_ADJUDICATION_QUEUE.jsonl').write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in fresh), encoding='utf-8')

    seen_counter = Counter()
    for r in rows:
        if not r['already_seen_classes']:
            seen_counter['FRESH'] += 1
        else:
            for c in r['already_seen_classes']:
                seen_counter[c] += 1
    kind_counter = Counter((r['supplier_kind'], r['consumer_kind']) for r in fresh)
    audit = {
        'release': 'R388_FULL_VISIBILITY_FRONTIER',
        'authority_status': 'SHADOW_ROUTING_NO_PRODUCT_PROMOTION',
        'candidate_universe_rows': len(rows),
        'active_candidate_rows': sum(bool(r.get('active_for_build', True)) for r in rows),
        'rejected_candidate_rows': sum(not bool(r.get('active_for_build', True)) for r in rows),
        'r386_carried_pair_count': sum(r['r386_disposition'] is not None for r in rows),
        'current_explicit_adjudication_pair_count': sum(r['current_adjudication_state'] is not None for r in rows),
        'canonical_executable_pair_count': sum(r['canonical_product_id'] is not None for r in rows),
        'shadow_executable_pair_count': sum(r['shadow_product_id'] is not None for r in rows),
        'fresh_adjudication_pair_count': len(fresh),
        'previously_hidden_parent_parent_pairs_total': sum(r['new_parent_parent_visibility'] for r in rows),
        'previously_hidden_parent_parent_pairs_fresh': sum(r['new_parent_parent_visibility'] and r['needs_fresh_adjudication'] for r in rows),
        'fresh_endpoint_kind_breakdown': {f'{a}_TO_{b}': n for (a,b), n in sorted(kind_counter.items())},
        'visibility_counts': dict(seen_counter),
        'policy': {
            'full_universe': 'persistent graph/research memory',
            'top1000_queue': 'bounded operational priority window only',
            'fresh_adjudication': 'pair has no carried R386 disposition, current explicit adjudication, canonical executable suite, or R388 shadow executable suite',
        },
        'nonclaims': [
            'fresh means previously unadjudicated, not novel',
            'native candidate compatibility is not a product claim',
            'routing priority is not scientific validation',
        ],
    }
    (HERE / 'R388_FULL_VISIBILITY_AUDIT.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
