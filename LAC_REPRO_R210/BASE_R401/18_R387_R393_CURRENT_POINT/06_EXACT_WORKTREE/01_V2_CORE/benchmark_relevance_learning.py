from __future__ import annotations
import json
from pathlib import Path

from lab_search_engine import LabSearchRouter, SearchQuery, load_search_corpus, InteractionGraph
from relevance_learning import (
    FeedbackEvent, FeedbackLedger, compile_relevance_snapshot,
    HELPED, HURT, LEARN_AFTER_GENERATION, PROTECTED_VALIDATION,
)

ROOT=Path(__file__).resolve().parent
CORPUS=ROOT/'generated_search'/'LAB_SEARCH_CORPUS.jsonl'
QUEUE=ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
QUERY_PATH=ROOT/'generated_search'/'EXAMPLE_PROBLEM_CONTRACT_CRYPTO_V1.json'
OUT=ROOT/'generated_search'/'RELEVANCE_LEARNING_LEAKAGE_GUARD_R3.json'
LEDGER_DEMO=ROOT/'generated_search'/'CRYPTO_V1_FEEDBACK_LEDGER_DEMO_R3.jsonl'
SNAPSHOT_OUT=ROOT/'generated_search'/'CRYPTO_V1_RELEVANCE_SNAPSHOT_G1_R3.json'


def ranks(result):
    return {h.document_id:i for i,h in enumerate(result.hits,1)}


def main():
    docs=load_search_corpus(CORPUS)
    graph=InteractionGraph.from_composition_queue(QUEUE)
    obj=json.loads(QUERY_PATH.read_text(encoding='utf-8'))
    q=SearchQuery.from_dict(obj,top_k=30)

    baseline_router=LabSearchRouter(docs,graph)
    baseline=baseline_router.search_capabilities(q,incremental=False)
    baseline_ids=tuple(h.document_id for h in baseline.hits)

    quarantine_only=FeedbackLedger([
        FeedbackEvent('same_generation_k069','LCB-K069',1,1,'crypto_algo_v1',HELPED,role=LEARN_AFTER_GENERATION,shell_tags=('crypto','algorithmic_trading')),
        FeedbackEvent('protected_validation_k071','LCB-K071',0,0,'crypto_algo_v1',HELPED,role=PROTECTED_VALIDATION,shell_tags=('crypto','algorithmic_trading')),
        FeedbackEvent('unrelated_shell_p137','FOUNDRY:P137',0,0,'clinical_decision',HURT,role=LEARN_AFTER_GENERATION,shell_tags=('clinical',)),
    ])
    quarantine_snapshot=compile_relevance_snapshot(quarantine_only,docs,target_generation=1,problem_shell='crypto_algo_v1',shell_tags=('crypto','algorithmic_trading','memory_selection'))
    quarantine_router=LabSearchRouter(docs,graph,relevance_snapshot=quarantine_snapshot)
    quarantine_result=quarantine_router.search_capabilities(q,incremental=False)
    quarantine_ids=tuple(h.document_id for h in quarantine_result.hits)

    ledger=FeedbackLedger(list(quarantine_only.events)+[
        FeedbackEvent(
            'k011_development_pass_g0','LCB-K011',0,0,'crypto_algo_v1',HELPED,
            role=LEARN_AFTER_GENERATION,shell_tags=('crypto','algorithmic_trading','memory_selection'),
            provenance={
                'artifact':'V2P046_K011_MAIN_FROZEN_EVALUATION.json',
                'source_status':'FROZEN_EXPERIMENTAL_CANDIDATE_NOT_ACTIVE',
                'basis':'development_pass=true; secondary_known_safe=true; untouched validation not performed',
            },
        ),
    ])
    ledger.save_jsonl(LEDGER_DEMO)
    snapshot=compile_relevance_snapshot(ledger,docs,target_generation=1,problem_shell='crypto_algo_v1',shell_tags=('crypto','algorithmic_trading','memory_selection'))
    snapshot.save(SNAPSHOT_OUT)
    learned_router=LabSearchRouter(docs,graph,relevance_snapshot=snapshot)
    learned=learned_router.search_capabilities(q,incremental=False)

    br=ranks(baseline); lr=ranks(learned)
    anchors=['FOUNDRY:P137','LCB-K071','LCB-K089','LCB-K011','LCB-K069']
    report={
        'benchmark':'R3 leakage-resistant relevance learning on real Lab search corpus',
        'documents':len(docs),
        'target_generation':1,
        'problem_shell':'crypto_algo_v1',
        'quarantine_only_top30_identical_to_baseline':quarantine_ids==baseline_ids,
        'quarantine_only_document_offsets':dict(quarantine_snapshot.document_offsets),
        'quarantine_reasons':list(quarantine_snapshot.quarantined_events),
        'eligible_learning_events':list(snapshot.included_event_ids),
        'learned_document_offsets':dict(snapshot.document_offsets),
        'anchor_ranks_before':{a:br.get(a) for a in anchors},
        'anchor_ranks_after':{a:lr.get(a) for a in anchors},
        'k011_prior':snapshot.document_offsets.get('LCB-K011',0.0),
        'k011_rank_before':br.get('LCB-K011'),
        'k011_rank_after':lr.get('LCB-K011'),
        'claim_scope':'Mechanics/leakage guard only. Rank movement after feeding a known development outcome is expected behavior, not independent evidence that learned relevance improves external discovery quality.',
    }
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
