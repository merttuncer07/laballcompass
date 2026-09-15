"""One-command R12 state refresh.

Order matters:
telemetry -> queue hydration -> typed interaction map -> simple-lexicon search corpus
-> campaign memory/state summary.
"""
from __future__ import annotations
from pathlib import Path
import csv, json, re

ROOT=Path(__file__).resolve().parent


def main()->dict:
    from telemetry_registry import write_registry
    ledger_path,index_path,index=write_registry(ROOT)

    import build_core_v2_foundry
    build_core_v2_foundry.main()
    # Queue rebuild does not alter telemetry; reload the generated canonical index.
    index=json.loads(index_path.read_text(encoding='utf-8'))

    from interaction_map import compile_interaction_map
    imap=compile_interaction_map(ROOT,telemetry_index=index)
    map_path=ROOT/'generated_search'/'INTERACTION_MAP_R12.json'
    imap.save(map_path)

    import build_search_corpus
    build_search_corpus.main()

    from campaign_memory import bootstrap_current_memory,save_events,load_events,build_summary,to_feedback_events
    system_events=bootstrap_current_memory(ROOT,index)
    campaign_path=ROOT/'search_data'/'CAMPAIGN_MEMORY.jsonl'
    existing=load_events(campaign_path)
    # Refresh owns only deterministic LAB_CORE ADJ/MECH rows; mission/campaign rows persist.
    mission_events=tuple(e for e in existing if not (e.campaign_id=='LAB_CORE' and (e.event_id.startswith('ADJ::') or e.event_id.startswith('MECH::'))))
    merged_by_id={e.event_id:e for e in mission_events}
    for e in system_events:
        if e.event_id in merged_by_id and merged_by_id[e.event_id].to_dict()!=e.to_dict():
            raise ValueError(f'campaign event conflict: {e.event_id}')
        merged_by_id[e.event_id]=e
    campaign_events=tuple(merged_by_id[k] for k in sorted(merged_by_id))
    save_events(campaign_path,campaign_events)
    campaign_summary=build_summary(campaign_events)

    # Close campaign -> relevance loop. Existing non-campaign feedback is retained;
    # campaign-derived rows are regenerated only from explicitly eligible evidence.
    from relevance_learning import FeedbackLedger
    feedback_path=ROOT/'search_data'/'FEEDBACK_LEDGER.jsonl'
    existing_feedback=FeedbackLedger.load_jsonl(feedback_path)
    keep=[e for e in existing_feedback.events if not e.event_id.startswith('CAMPAIGN::')]
    fb=FeedbackLedger(keep)
    for e in to_feedback_events(campaign_events): fb.append(e)
    fb.save_jsonl(feedback_path)

    queue=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
    universe_path=ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl'
    universe=[json.loads(x) for x in universe_path.read_text(encoding='utf-8').splitlines() if x.strip()] if universe_path.exists() else list(queue)
    corpus_meta=json.loads((ROOT/'generated_search'/'LAB_SEARCH_CORPUS_COUNTS.json').read_text(encoding='utf-8'))
    # Lexicon audit: canonical primitive text is independent of source/domain provenance.
    primitive_path=ROOT/'search_data'/'LABALLCOMPASS_CANONICAL_INVENTORY_4000.tsv'
    with primitive_path.open(encoding='utf-8') as f:
        prim_rows=list(csv.DictReader(f,delimiter='\t'))
    # Product authority is layered deliberately. R12's quality audit is historical base
    # authority; later executable overlays must never be smuggled into that file.
    base_quality_path=ROOT/'PRODUCT_QUALITY_AUDIT_V1.json'
    base_quality=json.loads(base_quality_path.read_text(encoding='utf-8')) if base_quality_path.exists() else {}
    # Use the newest explicitly materialized product overlay while preserving earlier
    # audits as immutable history.  An overlay is observational/candidate authority,
    # never a substitute for CURRENT_PRODUCT_AUTHORITY.json.
    # Discover release overlays dynamically so a new promoted/candidate release cannot
    # become invisible merely because this state summarizer predates its release number.
    overlay_candidates=[]
    for audit_path in ROOT.glob('PRODUCT_QUALITY_AUDIT_R*.json'):
        match=re.fullmatch(r'PRODUCT_QUALITY_AUDIT_R(\d+)\.json',audit_path.name)
        if not match:
            continue
        release=int(match.group(1))
        state_path=ROOT/f'R{release}_PRODUCT_OVERLAY_STATE.json'
        if state_path.exists():
            overlay_candidates.append((release,audit_path,state_path))
    if overlay_candidates:
        _,overlay_quality_path,overlay_state_path=max(overlay_candidates,key=lambda item:item[0])
    else:
        overlay_quality_path=ROOT/'PRODUCT_QUALITY_AUDIT_R386.json'
        overlay_state_path=ROOT/'R386_PRODUCT_OVERLAY_STATE.json'
    overlay_quality=json.loads(overlay_quality_path.read_text(encoding='utf-8')) if overlay_quality_path.exists() else {}
    overlay_state=json.loads(overlay_state_path.read_text(encoding='utf-8')) if overlay_state_path.exists() else {}
    authority_path=ROOT/'CURRENT_PRODUCT_AUTHORITY.json'
    authority=json.loads(authority_path.read_text(encoding='utf-8')) if authority_path.exists() else {}

    base_products=base_quality.get('raw_completed_executable_suites')
    base_families=base_quality.get('distinct_product_families')
    observed_suites=index['current_completed_suite_count']
    candidate_products=overlay_quality.get('resulting_executable_suite_count')
    candidate_families=overlay_quality.get('resulting_distinct_family_count')
    canonical_products=authority.get('canonical_executable_suite_count',base_products)
    canonical_families=authority.get('canonical_distinct_family_count',base_families)
    state={
        'engine':'LABALLCOMPASS_R12',
        'telemetry':{
            'canonical_ledger':str(ledger_path.relative_to(ROOT)),
            'events':index['event_count'],
            'completed_suites':index['current_completed_suite_count'],
            'calibrated_completed_suites':index['calibrated_current_suite_count'],
            'exact_current_suite_matches':index['exact_current_suite_matches'],
            'unmatched_events':index['unmatched_event_count'],
        },
        'interaction_map':{
            'path':str(map_path.relative_to(ROOT)),
            'nodes':len(imap.nodes),
            'node_counts':imap.to_dict()['node_counts'],
            'edges':len(imap.edges),
            'relation_counts':imap.to_dict()['relation_counts'],
            'fingerprint':imap.fingerprint,
        },
        'candidate_universe':{
            'rows':len(universe),
            'active_rows':sum(bool(r.get('active_for_build',True)) for r in universe),
            'rejected_rows':sum(not bool(r.get('active_for_build',True)) for r in universe),
            'persistence':'FULL_RANKED_UNIVERSE',
        },
        'queue':{
            'rows':len(queue),
            'role':'TOP_1000_OPERATIONAL_PRIORITY_WINDOW',
            'rows_with_standardized_telemetry':sum(r.get('experiment_telemetry_event_count',0)>0 for r in queue),
            'rows_with_exact_calibration':sum(r.get('experiment_calibration_status')=='CALIBRATED_EXACT_SHELL' for r in queue),
            'fixed_pilotable':sum(r.get('experiment_bootstrap_status')=='FIXED_PILOT_SCHEDULE_AVAILABLE' for r in queue),
        },
        'simple_lexicon':{
            'primitives':len(prim_rows),
            'canonical_identity_fields':['primitive','constraint_shell'],
            'provenance_only_fields':['domain','source_concept'],
            'search_documents':corpus_meta['documents'],
        },
        'campaign_memory':campaign_summary,
        'product_quality':{
            'policy':'PRODUCT_QUALITY_POLICY.md',
            'base_authority':{
                'audit':base_quality_path.name,
                'executable_suites':base_products,
                'distinct_families':base_families,
                'distinct_families_pre_quality_batch':base_quality.get('distinct_families_pre_quality_batch'),
                'new_distinct_products_batch4':base_quality.get('new_distinct_products_batch4'),
            },
            'candidate_overlay':{
                'audit':overlay_quality_path.name if overlay_quality_path.exists() else None,
                'state':overlay_state_path.name if overlay_state_path.exists() else None,
                'status':overlay_state.get('status'),
                'executable_suites':candidate_products,
                'distinct_families':candidate_families,
                'promoted_product_ids':overlay_quality.get('promoted_product_ids',[]),
                'candidate_added_suite_ids':overlay_quality.get('candidate_added_suite_ids',[]),
                'candidate_distinct_product_ids':overlay_quality.get('candidate_distinct_product_ids',[]),
                'quarantined_product_ids':overlay_quality.get('quarantined_product_ids',[]),
            },
            'canonical_product_authority':{
                'authority_file':authority_path.name if authority_path.exists() else None,
                'authority_release':authority.get('authority_release','R12'),
                'status':authority.get('status','BASE_AUTHORITY'),
                'registry_family_count':authority.get('registry_family_count',455),
                'registry455_unchanged':authority.get('registry455_unchanged',True),
                'executable_suites':canonical_products,
                'distinct_families':canonical_families,
            },
            'observed_executable_suites':observed_suites,
            'observed_matches_candidate_overlay': observed_suites==candidate_products if candidate_products is not None else None,
        },
        'nonclaims':[
            'bootstrap telemetry is mechanics/channel calibration, not scientific validation',
            'inferred composition queue rows are hypotheses, not known interaction-map truths',
            'domain/source labels remain searchable provenance aliases but do not define canonical primitive identity',
        ],
    }
    out=ROOT/'generated_search'/'LAB_STATE_R12.json'
    out.write_text(json.dumps(state,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(state,indent=2,ensure_ascii=False))
    return state

if __name__=='__main__': main()
