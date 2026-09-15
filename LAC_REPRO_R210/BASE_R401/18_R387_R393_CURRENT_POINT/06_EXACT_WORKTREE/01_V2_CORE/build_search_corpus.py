"""Build a rich LabAllCompass search corpus.

The search representation deliberately preserves mechanism descriptions and known
working/failure context instead of flattening every capability to a few tags.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

from simple_lexicon import CanonicalPrimitive

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl'
LCB_RICH = ROOT / 'generated' / 'CORE_V2_UNIFIED_REGISTRY.jsonl'
FOUNDRY_RICH = ROOT / 'generated' / 'FOUNDRY_PRODUCT_CATALOG.jsonl'
PARENTS_RICH = ROOT / 'generated' / 'FOUNDRY_PARENT_INTERFACE_REGISTRY.json'
PRIMITIVES = ROOT / 'search_data' / 'LABALLCOMPASS_CANONICAL_INVENTORY_4000.tsv'
OUT = ROOT / 'generated_search' / 'LAB_SEARCH_CORPUS.jsonl'
META = ROOT / 'generated_search' / 'LAB_SEARCH_CORPUS_COUNTS.json'


def _join(*parts: object) -> str:
    out=[]
    for p in parts:
        if p is None: continue
        if isinstance(p, str): out.append(p)
        elif isinstance(p, (list, tuple, set)):
            out.extend(str(x) for x in p)
        elif isinstance(p, dict):
            out.append(json.dumps(p, ensure_ascii=False))
        else: out.append(str(p))
    return ' '.join(x for x in out if x)


def _load_rich_text() -> dict[str, str]:
    rich: dict[str, str] = {}
    if LCB_RICH.exists():
        for line in LCB_RICH.read_text(encoding='utf-8').splitlines():
            if not line.strip(): continue
            r=json.loads(line)
            queue=[]
            for q in r.get('queue_matches', []):
                queue.extend([q.get('members',''), q.get('status',''), q.get('value_action',''), q.get('product_form',''), q.get('surfaces','')])
            rich[r['kernel_id']] = _join(
                r.get('class_name'), r.get('base_name'), r.get('docstring'),
                r.get('core_v2_role'), r.get('working_region'), r.get('failure_region'),
                r.get('router_or_fallback'), queue, r.get('retro50_relation', {}),
            )
    if FOUNDRY_RICH.exists():
        for line in FOUNDRY_RICH.read_text(encoding='utf-8').splitlines():
            if not line.strip(): continue
            r=json.loads(line)
            rich['FOUNDRY:'+r['product_id']] = _join(
                r.get('short_name'), r.get('title'), r.get('parents_raw'),
                r.get('promotion_state'), r.get('strength_raw'), r.get('weakness_raw'),
                r.get('evidence_raw'),
            )
    if PARENTS_RICH.exists():
        for r in json.loads(PARENTS_RICH.read_text(encoding='utf-8')):
            source_bits=[]
            for m in r.get('source_modules', []):
                source_bits.append(m.get('file',''))
                for c in m.get('classes', []):
                    source_bits.extend([c.get('name',''), c.get('docstring','')])
                    for method in c.get('methods', []):
                        source_bits.extend([method.get('name',''), method.get('signature',''), method.get('return_annotation','')])
            rich['PARENT:'+r['product_dir']] = _join(
                r.get('product_dir'), r.get('readme_summary'), source_bits,
                [x.get('file','') for x in r.get('test_files', [])],
                r.get('tested_public_callables', []),
            )
    return rich


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rich=_load_rich_text()
    docs=[]
    for line in REGISTRY.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        r=json.loads(line)
        text=_join(
            r.get('name'), r.get('family'), r.get('evidence_tier'),
            r.get('strength_tags',[]), r.get('weakness_tags',[]),
            r.get('input_types',[]), r.get('output_types',[]),
            rich.get(r['capability_id'], ''), r.get('source',{}),
        )
        docs.append({
            'document_id': r['capability_id'], 'name': r['name'], 'family': r['family'],
            'text': text, 'strength_tags': r.get('strength_tags',[]),
            'weakness_tags': r.get('weakness_tags',[]),
            'input_types': r.get('input_types',[]), 'output_types': r.get('output_types',[]),
            'domains': [], 'evidence_tier': r.get('evidence_tier',''),
            'standalone_value': r.get('standalone_value',0), 'component_value': r.get('component_value',0),
            'metadata': {'kind':'capability','source':r.get('source',{}), 'rich_text_present': bool(rich.get(r['capability_id']))},
        })
    with PRIMITIVES.open(encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            cp=CanonicalPrimitive.from_row(r)
            docs.append({
                'document_id':'PRIMITIVE:'+r['id'], 'name':cp.canonical_text, 'family':'PRIMITIVE',
                'text':cp.canonical_text, 'strength_tags':[], 'weakness_tags':[], 'input_types':[], 'output_types':[],
                # Domain remains an explicit query filter/provenance field, not canonical mechanism text.
                'domains':[r['domain'].lower()], 'evidence_tier':'PRIMITIVE_INVENTORY',
                'standalone_value':0, 'component_value':0,
                'metadata':{
                    'kind':'primitive','primitive_id':r['id'],'domain':r['domain'],
                    'source_concept':r['source_concept'],'search_aliases':list(cp.aliases),
                    'primitive':r['primitive'],'constraint_shell':r['constraint_shell'],
                    'canonical_fingerprint':cp.canonical_fingerprint,
                },
            })
    ids=[d['document_id'] for d in docs]
    if len(ids)!=len(set(ids)): raise RuntimeError('duplicate search document ids')
    OUT.write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in docs), encoding='utf-8')
    meta={
        'documents':len(docs),
        'capabilities':sum(d['family']!='PRIMITIVE' for d in docs),
        'primitives':sum(d['family']=='PRIMITIVE' for d in docs),
        'capabilities_with_rich_text':sum(d['metadata'].get('rich_text_present',False) for d in docs),
    }
    META.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(meta))

if __name__=='__main__': main()
