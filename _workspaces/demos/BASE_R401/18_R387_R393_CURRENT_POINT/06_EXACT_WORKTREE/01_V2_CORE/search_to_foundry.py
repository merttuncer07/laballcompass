"""Turn a research problem contract into a Foundry search packet.

This is the bridge from retrieval to product generation. It deliberately keeps
three evidence surfaces separate:
  1) direct executable/capability matches,
  2) primitive mechanism donors,
  3) interaction-map expansions around directly relevant capabilities.

The packet proposes what to inspect/compose next; it does not promote products.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from typing import Mapping

from core_v2 import build_search_router
from lab_search_engine import SearchQuery

ROOT=Path(__file__).resolve().parent
QUEUE=ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
INTERACTION_MAP=ROOT/'generated_search'/'INTERACTION_MAP_R12.json'


def _problem_text(obj: Mapping[str,object]) -> str:
    parts=[]
    for k in ('objective','diagnosed_failure','mechanism_needs','allowed_interventions','text','query'):
        v=obj.get(k)
        if isinstance(v,str): parts.append(v)
        elif isinstance(v,list): parts.extend(str(x) for x in v)
    return ' '.join(parts)


def _hit_dict(engine, hit, query, rank):
    return {
        'rank':rank,
        'document_id':hit.document_id,
        'name':hit.name,
        'family':hit.family,
        'score':round(hit.score,6),
        'metadata':dict(hit.metadata),
        'score_explanation':engine.explain_score(hit.document_id,query,limit=10),
    }


def build_packet(problem: Mapping[str,object], *, capability_k:int=24, primitive_k:int=20, expansion_seeds:int=8, suppliers_per_seed:int=6, router=None, incremental:bool=True, relevance_snapshot=None, experiment_calibration_snapshot=None) -> dict:
    router=router or build_search_router(relevance_snapshot=relevance_snapshot)
    base_query=SearchQuery.from_dict(problem,top_k=capability_k)
    cap=router.search_capabilities(base_query,incremental=incremental)
    capabilities=[_hit_dict(router.capability_engine,h,base_query,i) for i,h in enumerate(cap.hits,1)]

    # Pull a larger primitive pool, then prevent one donor domain from monopolizing the packet.
    primitive_query=SearchQuery.from_dict(problem,top_k=max(primitive_k*4,primitive_k))
    prim=router.discover_primitives(primitive_query,incremental=incremental)
    per_domain={}; primitive_rows=[]; selected=set()
    for h in prim.hits:
        domain=str(h.metadata.get('domain','UNKNOWN'))
        if per_domain.get(domain,0)>=2: continue
        per_domain[domain]=per_domain.get(domain,0)+1
        selected.add(h.document_id)
        primitive_rows.append(_hit_dict(router.primitive_engine,h,primitive_query,len(primitive_rows)+1))
        if len(primitive_rows)>=primitive_k: break
    # Diversity is a preference, not a quota that is allowed to shrink recall.
    # If the first pass cannot fill the requested frontier, backfill by score.
    if len(primitive_rows)<primitive_k:
        for h in prim.hits:
            if h.document_id in selected: continue
            selected.add(h.document_id)
            primitive_rows.append(_hit_dict(router.primitive_engine,h,primitive_query,len(primitive_rows)+1))
            if len(primitive_rows)>=primitive_k: break

    queue_rows=json.loads(QUEUE.read_text(encoding='utf-8')) if QUEUE.exists() else []
    queue_by_pair={(str(r.get('supplier_id')),str(r.get('consumer_id'))):r for r in queue_rows}
    typed_map=None
    if INTERACTION_MAP.exists():
        from interaction_map import load_interaction_map, COMPLETED, CURATED, PARENT_OF
        typed_map=load_interaction_map(INTERACTION_MAP)
        map_relations=(COMPLETED,CURATED,PARENT_OF)
    else:
        map_relations=()
    objective=_problem_text(problem)
    expansions=[]; seen=set()
    for seed_rank,seed in enumerate(cap.hits[:expansion_seeds],1):
        known=[]
        if typed_map is not None:
            for n in typed_map.neighbors(seed.document_id,relations=map_relations,active_only=True):
                medge=n['edge']; rel=medge['relation']; neighbor_id=n['neighbor_id']
                if rel in ('COMPLETED_COMPOSITION','CURATED_HYPOTHESIS'):
                    if n['direction']=='IN': direction='UPSTREAM_SUPPLIER'
                    else: direction='DOWNSTREAM_CONSUMER'
                    pair=(medge['source_id'],medge['target_id'])
                    qedge=queue_by_pair.get(pair)
                else:
                    # Historical provenance parents remain in the typed map but are
                    # not searchable capabilities unless they exist in the router.
                    if neighbor_id not in router.by_id:
                        continue
                    direction='UPSTREAM_PARENT' if n['direction']=='IN' else 'DOWNSTREAM_PRODUCT'
                    qedge=None
                known.append((rel,direction,neighbor_id,medge,qedge))
        for rel,direction,neighbor_id,medge,qedge in known[:suppliers_per_seed]:
            key=(seed.document_id,direction,neighbor_id,rel)
            if key in seen: continue
            seen.add(key)
            neighbor=router.by_id.get(neighbor_id)
            expansions.append({
                'seed_rank':seed_rank,'seed_id':seed.document_id,'seed_name':seed.name,
                'direction':direction,'neighbor_id':neighbor_id,'neighbor_name':neighbor.name if neighbor else neighbor_id,
                'known_interaction':True,'interaction_relation':rel,'interaction_edge':medge,
                'edge':qedge,
            })
        if not known:
            # No explicit typed interaction is known. Supplier search may propose a
            # hypothesis; it is not promoted into the map until adjudicated/completed.
            result=router.search_suppliers(seed.document_id,objective,top_k=min(3,suppliers_per_seed),incremental=incremental)
            for rank,h in enumerate(result.hits,1):
                key=(seed.document_id,'HYPOTHETICAL_UPSTREAM',h.document_id)
                if key in seen: continue
                seen.add(key)
                expansions.append({
                    'seed_rank':seed_rank,'seed_id':seed.document_id,'seed_name':seed.name,
                    'direction':'HYPOTHETICAL_UPSTREAM','neighbor_id':h.document_id,'neighbor_name':h.name,
                    'hypothesis_rank':rank,'known_interaction':False,'interaction_relation':'SEARCH_HYPOTHESIS',
                })
    expansions.sort(key=lambda x:(x['seed_rank'],0 if x.get('known_interaction') else 1,x.get('direction',''),x.get('neighbor_id','')))
    bootstrap_opportunities=[]
    seen_bootstrap=set()
    for x in expansions:
        edge=x.get('edge') if x.get('known_interaction') else None
        if isinstance(edge,Mapping) and edge.get('experiment_bootstrap_status') == 'FIXED_PILOT_SCHEDULE_AVAILABLE':
            key=(edge.get('supplier_id'),edge.get('consumer_id'),edge.get('experiment_bootstrap_product_id'))
            if key in seen_bootstrap:
                continue
            seen_bootstrap.add(key)
            bootstrap_opportunities.append({
                'supplier_id':edge.get('supplier_id'),'consumer_id':edge.get('consumer_id'),
                'product_id':edge.get('experiment_bootstrap_product_id'),
                'case_count':edge.get('experiment_bootstrap_case_count'),
                'problem_shell':edge.get('experiment_bootstrap_problem_shell'),
                'status':'FIXED_NONADAPTIVE_PILOT_AVAILABLE_NUMERIC_ROUTING_STILL_UNKNOWN',
            })

    experiment_gate = {
        'status':'NOT_READY_WITHOUT_DECLARED_EXPERIMENT_CONTRACT',
        'policy':'do not infer information gain, reliability, or compute cost from prose',
        'required_fields':['decision_id','uncertainty_axes','test_channels[*].test_signature','test_channels[*].expected_resolution_by_axis','test_channels[*].compute_seconds','test_channels[*].reliability','test_channels[*].calibration_id','test_channels[*].measurement_backreaction','test_channels[*].backreaction_adjusted','test_channels[*].evidence_role','test_channels[*].selection_generation'],
    }
    raw_experiment = problem.get('experiment_contract')
    if isinstance(raw_experiment, Mapping):
        from experiment_selector import contract_from_dict, choose_next_experiment
        exp_contract = contract_from_dict(raw_experiment)
        calibration_fp = None
        calibration_source = None
        # R12 precedence rule: an already-complete declared experiment contract is
        # authoritative for this routing call. Canonical telemetry may fill UNKNOWN
        # fields, but it must not relabel or override a fully declared contract.
        needs_calibration = any(
            t.compute_seconds is None
            or t.reliability is None
            or not t.calibration_id
            or t.measurement_backreaction is None
            or (t.measurement_backreaction is True and not t.backreaction_adjusted)
            or any(v is None for axis, v in t.expected_resolution_by_axis.items()
                   if axis in {a.axis_id for a in exp_contract.axes})
            for t in exp_contract.tests
        )
        snap = experiment_calibration_snapshot if needs_calibration else None
        if snap is None and needs_calibration:
            canonical_ledger=ROOT/'search_data'/'EXPERIMENT_TELEMETRY.jsonl'
            if canonical_ledger.exists():
                from experiment_telemetry import ExperimentTelemetryLedger, compile_calibration_snapshot
                snap=compile_calibration_snapshot(
                    ExperimentTelemetryLedger.load_jsonl(canonical_ledger),
                    target_generation=exp_contract.search_generation,
                    problem_shell=exp_contract.problem_shell,
                )
                calibration_source='CANONICAL_TELEMETRY_LEDGER'
        if snap is not None:
            from experiment_telemetry import ExperimentCalibrationSnapshot, hydrate_contract_from_calibration
            if isinstance(snap, (str, Path)):
                snap = ExperimentCalibrationSnapshot.load(snap)
                calibration_source=calibration_source or 'EXPLICIT_SNAPSHOT_PATH'
            elif isinstance(snap, Mapping):
                snap = ExperimentCalibrationSnapshot.from_dict(snap)
                calibration_source=calibration_source or 'EXPLICIT_SNAPSHOT_OBJECT'
            else:
                calibration_source=calibration_source or 'EXPLICIT_SNAPSHOT'
            exp_contract = hydrate_contract_from_calibration(exp_contract, snap)
            calibration_fp = snap.fingerprint
        plan = choose_next_experiment(exp_contract)
        if calibration_fp is not None and plan.selected_test_id is None and plan.unquantified_test_ids:
            status='NOT_READY_CALIBRATION_INSUFFICIENT'
        elif calibration_fp is not None:
            status='ROUTED_FROM_FROZEN_AUTO_CALIBRATION'
        else:
            status='ROUTED_FROM_DECLARED_CONTRACT'
        experiment_gate = {
            'status':status,
            'calibration_snapshot_fingerprint':calibration_fp,
            'calibration_source':calibration_source,
            'plan':plan.to_dict(),
        }

    telemetry_index_path=ROOT/'generated_search'/'EXPERIMENT_TELEMETRY_INDEX_R12.json'
    telemetry_fp=None
    if telemetry_index_path.exists():
        telemetry_fp=json.loads(telemetry_index_path.read_text(encoding='utf-8')).get('fingerprint')
    interaction_fp=getattr(typed_map,'fingerprint',None)
    packet = {
        'engine':'LABALLCOMPASS_SEARCH_TO_FOUNDRY_R12',
        'problem_id':problem.get('problem_id','UNSPECIFIED'),
        'search_generation':(getattr(relevance_snapshot,'target_generation',None) if relevance_snapshot is not None else problem.get('search_generation')),
        'relevance_snapshot_fingerprint':getattr(relevance_snapshot,'fingerprint',None),
        'contract':dict(problem),
        'semantics':{
            'capabilities':'direct problem relevance only; interaction graph not allowed to inflate first-stage relevance',
            'primitives':'direct donor retrieval with max two selected donors per source domain',
            'interaction_expansions':'directly relevant capability is identity-seeded, then only typed completed/curated/parent interactions are traversed as known map edges; inferred queue rows remain hypotheses and rejected interfaces remain explicit negative map knowledge',
            'promotion':'none; this packet is a search/frontier artifact, not product evidence',
            'relevance_learning':'optional frozen prior from closed earlier search generations; same-generation and protected-validation outcomes are excluded by construction',
            'experiment_selection':'next-test routing uses declared contracts; R12 uses the canonical telemetry ledger/index to fill only UNKNOWN fields through the existing exact-shell/exact-signature conservative calibration; bootstrap case coverage remains mechanics telemetry, not scientific validation',
        },
        'direct_capabilities':capabilities,
        'primitive_donors':primitive_rows,
        'interaction_expansions':expansions,
        'relevance_snapshot':(relevance_snapshot.to_dict() if relevance_snapshot is not None and hasattr(relevance_snapshot,'to_dict') else None),
        'experiment_selection':experiment_gate,
        'experiment_bootstrap_opportunities':bootstrap_opportunities,
        'research_trace':{
            'campaign_id':problem.get('campaign_id'),
            'interaction_map_fingerprint':interaction_fp,
            'telemetry_registry_fingerprint':telemetry_fp,
            'direct_capability_ids':[x['document_id'] for x in capabilities],
            'primitive_donor_ids':[x['document_id'] for x in primitive_rows],
            'interaction_pairs':[(x.get('seed_id'),x.get('neighbor_id'),x.get('interaction_relation')) for x in expansions],
            'purpose':'future campaign outcomes can cite this frozen search packet; this trace is not evidence by itself',
        },
        'counts':{
            'capabilities_returned':len(capabilities),
            'primitive_donors_returned':len(primitive_rows),
            'interaction_expansions_returned':len(expansions),
        },
    }
    raw=json.dumps(packet,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    packet['packet_fingerprint']=hashlib.sha256(raw).hexdigest()
    return packet


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--query',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--feedback-ledger',type=Path)
    ap.add_argument('--generation',type=int)
    ap.add_argument('--problem-shell')
    ap.add_argument('--shell-tags',nargs='*')
    ap.add_argument('--relevance-snapshot-output',type=Path)
    ap.add_argument('--experiment-telemetry-ledger',type=Path)
    ap.add_argument('--experiment-calibration-output',type=Path)
    args=ap.parse_args()
    obj=json.loads(args.query.read_text(encoding='utf-8'))
    relevance_snapshot=None
    if args.feedback_ledger is not None:
        if args.generation is None:
            raise SystemExit('--generation is required with --feedback-ledger')
        from core_v2 import compile_search_relevance_snapshot
        shell=args.problem_shell or str(obj.get('problem_shell',obj.get('problem_id','UNSPECIFIED')))
        tags=(args.shell_tags if args.shell_tags is not None else obj.get('shell_tags',()))
        relevance_snapshot=compile_search_relevance_snapshot(args.feedback_ledger,target_generation=args.generation,problem_shell=shell,shell_tags=tags)
        if args.relevance_snapshot_output is not None:
            relevance_snapshot.save(args.relevance_snapshot_output)
    experiment_calibration_snapshot=None
    if args.experiment_telemetry_ledger is not None:
        raw=obj.get('experiment_contract')
        if not isinstance(raw,dict):
            raise SystemExit('--experiment-telemetry-ledger requires experiment_contract in query JSON')
        from core_v2 import compile_experiment_calibration_snapshot
        generation=int(raw.get('search_generation',obj.get('search_generation',0)))
        shell=str(raw.get('problem_shell',obj.get('problem_shell',obj.get('problem_id','UNSPECIFIED'))))
        experiment_calibration_snapshot=compile_experiment_calibration_snapshot(args.experiment_telemetry_ledger,target_generation=generation,problem_shell=shell)
        if args.experiment_calibration_output is not None:
            experiment_calibration_snapshot.save(args.experiment_calibration_output)
    packet=build_packet(obj,relevance_snapshot=relevance_snapshot,experiment_calibration_snapshot=experiment_calibration_snapshot)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(packet['counts']))

if __name__=='__main__': main()
