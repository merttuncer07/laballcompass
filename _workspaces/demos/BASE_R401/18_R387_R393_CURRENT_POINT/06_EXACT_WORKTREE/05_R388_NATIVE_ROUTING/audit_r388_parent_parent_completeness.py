from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
CORE = LAB / '01_V2_CORE'
sys.path.insert(0, str(CORE))

from core_v2 import CapabilityProfile, rank_composition
from build_core_v2_foundry import evidence_weight

REG = CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl'
QUEUE = CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
PARENTS = CORE / 'generated' / 'FOUNDRY_PARENT_INTERFACE_REGISTRY.json'
OUT = HERE / 'R388_PARENT_PARENT_COMPLETENESS_AUDIT.json'
CANDIDATES = HERE / 'R388_PARENT_PARENT_PREVIOUSLY_HIDDEN_CANDIDATES.jsonl'


def load_jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def main():
    rows = load_jsonl(REG)
    by_id = {r['capability_id']: r for r in rows}
    profiles = {
        r['capability_id']: CapabilityProfile(
            r['capability_id'], r['name'], r['family'], r['evidence_tier'],
            frozenset(r['strength_tags']), frozenset(r['weakness_tags']),
            frozenset(r['input_types']), frozenset(r['output_types']),
            r['standalone_value'], r['component_value'],
        )
        for r in rows
    }
    parent_rows = json.loads(PARENTS.read_text(encoding='utf-8'))
    parent_kind = {
        'PARENT:' + r['product_dir']: ('RETRO' if 'RETRO_PRODUCTS' in str(r.get('relative_path', '')) else 'CURRENT_PARENT')
        for r in parent_rows
    }
    parent_ids = set(parent_kind)
    assert len(parent_ids) == 69
    assert Counter(parent_kind.values()) == Counter({'RETRO': 50, 'CURRENT_PARENT': 19})

    hidden = []
    for sid in sorted(parent_ids):
        for cid in sorted(parent_ids):
            if sid == cid:
                continue
            supplier, consumer = profiles[sid], profiles[cid]
            c = rank_composition(
                supplier, consumer,
                evidence_weight=evidence_weight(supplier.evidence_tier) + evidence_weight(consumer.evidence_tier),
            )
            if c is None:
                continue
            hidden.append({
                'supplier_id': c.supplier_id,
                'consumer_id': c.consumer_id,
                'supplier_kind': parent_kind[c.supplier_id],
                'consumer_kind': parent_kind[c.consumer_id],
                'score': c.score,
                'interface_matches': list(c.interface_matches),
                'addressed_weaknesses': list(c.addressed_weaknesses),
                'shared_domains': list(c.shared_domains),
                'legacy_exclusion_reason': 'supplier.family == consumer.family == FOUNDRY_PARENT',
            })
    hidden.sort(key=lambda r: (-r['score'], r['supplier_id'], r['consumer_id']))

    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    top_parent_pairs = [
        r for r in queue
        if r['supplier_id'] in parent_ids and r['consumer_id'] in parent_ids
    ]

    breakdown = Counter((r['supplier_kind'], r['consumer_kind']) for r in hidden)
    audit = {
        'release': 'R388_PARENT_PARENT_COMPLETENESS',
        'authority_status': 'SHADOW_ANALYSIS_NO_PRODUCT_PROMOTION',
        'problem': 'FOUNDRY_PARENT is a provenance bucket, not a semantic equivalence family; the legacy same-family guard hid every parent-to-parent composition before rank/adjudication visibility.',
        'parent_record_count': len(parent_ids),
        'retro_parent_count': sum(v == 'RETRO' for v in parent_kind.values()),
        'current_parent_count': sum(v == 'CURRENT_PARENT' for v in parent_kind.values()),
        'directed_parent_pairs_before_compatibility': len(parent_ids) * (len(parent_ids) - 1),
        'native_rank_compatible_parent_pairs_previously_hidden': len(hidden),
        'breakdown': {f'{a}_TO_{b}': n for (a, b), n in sorted(breakdown.items())},
        'parent_parent_edges_now_visible_in_top1000_queue': len(top_parent_pairs),
        'coverage_claim': 'All 69 parent records are now allowed to reach native rank_composition against one another; incompatibility may still return no candidate and later adjudication may reject/collapse a candidate.',
        'nonclaims': [
            'visibility is not novelty',
            'candidate status is not product status',
            'adjudication remains responsible for semantic duplicate, ancestry, interface, and usefulness decisions',
        ],
    }
    OUT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    CANDIDATES.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in hidden), encoding='utf-8')
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
