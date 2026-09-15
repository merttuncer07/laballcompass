from __future__ import annotations
import json, random, time
from collections import Counter
from dataclasses import replace
from pathlib import Path

from core_v2 import build_search_router
from lab_search_engine import SearchQuery

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'generated_search'/'LAB_SEARCH_ENGINE_BENCHMARK_R12.json'
BASE={
  'objective':'Distinguish harmful fresh long theses from profitable persistence using causal information and local intervention.',
  'diagnosed_failure':['loss concentrated in small bad blocks','global filters erase profitable exposure'],
  'mechanism_needs':['adaptive selection holdout audit','memory lag validation','residual transport gate','predictable variance alarm','decision boundary sensitivity','localized router'],
  'search_terms':['holdout','selection','reference law','memory','lag','drift','residual','transport','predictable variance','alarm','decision','boundary','support','diversity','router','gate','invariance'],
  'priority_phrases':{'predictable variance':9.0,'memory kernel closure':8.0,'guarantee transport':7.0,'decision fluctuation':6.0,'lag':3.0},
  'preferred_strength_tags':['audit','selection','dynamics','decision','boundary','support','uncertainty','transport','control'],
  'available_input_types':['state','evidence','representation','metric','boundary','gate'],
  'preferred_output_types':['gate','report','representation','boundary','action'],
  'top_k':20,
}
TEXT_POOL=['persistence','nonstationary','abstain','calibration','regime','surprise','memory','selection','transport','boundary','tail','capacity','cycle','allocation','foobar_unmatched']
TAG_POOL=['audit','selection','dynamics','decision','boundary','support','uncertainty','transport','control','graph','allocation','measurement']


def exercise(engine,q,events,rng):
    first=engine.full_search(q); assert tuple(h.document_id for h in first.hits)==engine.naive_top_ids(q)
    active=set(q.text.split()); tags=set(q.preferred_strength_tags); statuses=Counter(); rescored=affected=mismatches=0
    for i in range(events):
        if i%4 in (0,1,2):
            w=rng.choice(TEXT_POOL); active.remove(w) if w in active else active.add(w); q=replace(q,text=' '.join(sorted(active)))
        else:
            t=rng.choice(TAG_POOL); tags.remove(t) if t in tags else tags.add(t); q=replace(q,preferred_strength_tags=tuple(sorted(tags)))
        r=engine.update(q); expected=engine.naive_top_ids(q); got=tuple(h.document_id for h in r.hits)
        if got!=expected: mismatches+=1; raise AssertionError((i,got,expected))
        statuses[r.status]+=1; rescored+=r.exact_rescored_this_update; affected+=r.documents_affected_by_delta
    return {'documents':len(engine._ids),'mismatches':mismatches,'initial_exact':len(engine._ids),'incremental_exact':rescored,'actual_exact':engine.exact_score_computations,'naive_exact':(events+1)*len(engine._ids),'reduction':1-engine.exact_score_computations/((events+1)*len(engine._ids)),'mean_rescore':rescored/events,'mean_affected':affected/events,'statuses':dict(statuses)}


def main():
    router=build_search_router(); q=SearchQuery.from_dict(BASE); events=60; rng=random.Random(20260826); t0=time.perf_counter()
    capability=exercise(router.capability_engine,q,events,rng)
    rng=random.Random(20260826); primitive=exercise(router.primitive_engine,q,events,rng)
    actual=capability['actual_exact']+primitive['actual_exact']; naive=capability['naive_exact']+primitive['naive_exact']
    payload={'engine_version':'R12 typed-map + simple-lexicon corpus','claim_scope':'actual Lab search surfaces (310 capabilities + 4,000 primitives), 60 deterministic query edits, every incremental top-k checked against exact full scoring of the same transparent scoring function; no production latency claim.', 'updates':events,'top_k':q.top_k,'capability_surface':capability,'primitive_surface':primitive,'combined_documents':4310,'combined_actual_exact_score_computations':actual,'combined_naive_exact_score_computations':naive,'combined_reduction_fraction':1-actual/naive,'wall_seconds_including_naive_verification':time.perf_counter()-t0}
    OUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(payload,indent=2))
if __name__=='__main__': main()
