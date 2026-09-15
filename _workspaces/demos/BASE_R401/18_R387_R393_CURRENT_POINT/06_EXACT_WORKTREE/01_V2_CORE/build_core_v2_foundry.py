from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from core_v2 import CapabilityProfile, rank_composition


ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parent
OUT=ROOT/'generated_v2_foundry'
LCB=ROOT/'generated'/'CORE_V2_UNIFIED_REGISTRY.jsonl'
PARENTS=ROOT/'generated'/'FOUNDRY_PARENT_INTERFACE_REGISTRY.json'
FOUNDRY=WORKSPACE/'02_FOUNDRY_ALL_PRODUCTS'/'audit'/'PRODUCT_EVIDENCE_INVENTORY.jsonl'
ADJUDICATIONS=ROOT/'COMPOSITION_EDGE_ADJUDICATIONS.jsonl'

DOMAIN_WORDS={
 'decision':('decision','regret','action'), 'selection':('selection','holdout','adaptive'),
 'support':('support','overlap','propensity'), 'uncertainty':('uncertainty','variance','error'),
 'measurement':('measurement','sensor','sampling','information','acquisition'),
 'allocation':('allocation','allocator','budget','portfolio','capacity'),
 'audit':('audit','guard','certificate','validation','verify'),
 'boundary':('tipping','threshold','boundary','cliff'), 'reduction':('reduction','compress','state'),
 'resilience':('resilience','recovery','hidden mode','damage'), 'transport':('transport','flow','deployable'),
 'conservation':('conservation','mass','source/sink'), 'integrality':('integral','integer','unimodular'),
 'causal':('causal','confound','treatment'), 'calibration':('calibration','calibrated'),
 'finance':('liquidity','funding','mortgage','capital'), 'control':('control','policy','controller'),
 'graph':('graph','network','cycle'), 'incentive':('contract','persuasion','incentive'),
 'dynamics':('dynamic','transient','persistence','memory'), 'risk':('risk','failure','fragility'),
}


def tags(text:str)->set[str]:
    value=text.lower(); return {tag for tag,words in DOMAIN_WORDS.items() if any(word in value for word in words)}


def io_types(text:str)->tuple[set[str],set[str],set[str]]:
    value=text.lower(); strength=tags(value); inputs={'state'}; outputs={'report'}
    if any(x in value for x in ('audit','guard','certificate','validation','verify')):
        inputs|={'evidence','representation'}; outputs|={'gate'}; strength|={'audit'}
    if any(x in value for x in ('sensor','sampling','measurement','information','acquisition')):
        outputs|={'evidence'}; strength|={'measurement'}
    if any(x in value for x in ('allocator','allocation','optimizer','controller','planner','policy')):
        inputs|={'evidence','gate','representation','boundary'}; outputs|={'action','allocation'}; strength|={'allocation'}
    if any(x in value for x in ('tipping','threshold','boundary','cliff')):
        inputs|={'metric','representation'}; outputs|={'boundary','gate'}; strength|={'boundary'}
    if any(x in value for x in ('reduction','compress','state','closure')):
        inputs|={'evidence'}; outputs|={'representation'}; strength|={'reduction'}
    weakness=set()
    if 'allocation' in strength:weakness|={'support','uncertainty','calibration'}
    if 'audit' in strength:weakness|={'transfer','calibration'}
    if 'measurement' in strength:weakness|={'confounding','decision'}
    if 'reduction' in strength:weakness|={'decision','resilience'}
    if 'boundary' in strength:weakness|={'calibration','transfer'}
    if not weakness:weakness={'calibration','transfer'}
    return strength,weakness,inputs,outputs


def evidence_weight(tier:str)->float:
    value=tier.upper()
    if 'ORIGINAL_EXECUTABLE' in value or 'MECHANISM_BENCHMARKED' in value:return 4
    if 'SALVAGED_SOURCE' in value or 'EXECUTABLE' in value:return 3
    if 'MECHANISM_RECONSTRUCTED' in value:return 2
    if 'SPEC_EXECUTABLE' in value:return 1
    if 'REPLACEMENT' in value or 'RESULT' in value:return 0
    return 1


def profile_record(capability_id,name,family,tier,text,standalone,component,extra=None):
    strength,weakness,inputs,outputs=io_types(text)
    return {'capability_id':capability_id,'name':name,'family':family,'evidence_tier':tier,'strength_tags':sorted(strength),'weakness_tags':sorted(weakness),'input_types':sorted(inputs),'output_types':sorted(outputs),'standalone_value':standalone,'component_value':component,'source':extra or {}}


def main():
    OUT.mkdir(exist_ok=True)
    records=[]; lcb_by_name={}
    for line in LCB.read_text(encoding='utf-8').splitlines():
        row=json.loads(line); name=row.get('class_name') or row.get('base_name') or row['kernel_id']; text=' '.join(str(row.get(k,'')) for k in ('class_name','base_name','core_v2_role','working_region','failure_region'))
        role=row['core_v2_role']; standalone=3 if 'CANDIDATE' in role or 'ACTION' in role else 1; component=3 if 'COMPONENT' in role or 'ASSURANCE' in role else 2
        record=profile_record(row['kernel_id'],name,'LCB_KERNEL',row['evidence_state'],text,standalone,component,{'origin':row['origin'],'adoption_state':row['adoption_state']})
        records.append(record); lcb_by_name[name]=record['capability_id']
    for row in json.loads(PARENTS.read_text(encoding='utf-8')):
        name=row['product_dir']; text=name+' '+row.get('readme_summary','')+' '+' '.join(m['file'] for m in row.get('source_modules',[]))
        records.append(profile_record('PARENT:'+name,name,'FOUNDRY_PARENT','ORIGINAL_EXECUTABLE_PARENT',text,3,3,{'test_methods':row.get('test_method_count',0),'relative_path':row.get('relative_path')}))
    for line in FOUNDRY.read_text(encoding='utf-8').splitlines():
        row=json.loads(line); text=' '.join([row['title'],row.get('parents',''),' '.join(row['tags']),' '.join(row['strengths']),' '.join(row['weaknesses'])])
        standalone=3 if row.get('execution_mode') in ('selection','allocation') else 2; component=3 if row.get('execution_mode') in ('audit','tipping') else 2
        rec=profile_record('FOUNDRY:'+row['product_id'],row['product_id']+' '+row['short_name'],'FOUNDRY_PRODUCT',row['tier'],text,standalone,component,{'title':row['title'],'parents':row.get('parents')})
        rec['strength_tags']=sorted(set(rec['strength_tags'])|set(row['tags'])); records.append(rec)
    assert len(records)==310
    profiles={r['capability_id']:CapabilityProfile(r['capability_id'],r['name'],r['family'],r['evidence_tier'],frozenset(r['strength_tags']),frozenset(r['weakness_tags']),frozenset(r['input_types']),frozenset(r['output_types']),r['standalone_value'],r['component_value']) for r in records}
    candidates={}
    for supplier in profiles.values():
        for consumer in profiles.values():
            if supplier.capability_id==consumer.capability_id:continue
            # `family` is a semantic family for LCB/Foundry products, but `FOUNDRY_PARENT`
            # is only a provenance bucket containing 69 distinct executable parents.
            # Treating that bucket as a semantic family hid the entire parent→parent
            # composition surface. Preserve same-family suppression everywhere else.
            if supplier.family==consumer.family and supplier.family!='FOUNDRY_PARENT':continue
            if 'FOUNDRY' not in supplier.family and 'FOUNDRY' not in consumer.family:continue
            c=rank_composition(supplier,consumer,evidence_weight=evidence_weight(supplier.evidence_tier)+evidence_weight(consumer.evidence_tier))
            if c:
                candidates[(c.supplier_id,c.consumer_id)]={'supplier_id':c.supplier_id,'consumer_id':c.consumer_id,'score':c.score,'interface_matches':list(c.interface_matches),'addressed_weaknesses':list(c.addressed_weaknesses),'shared_domains':list(c.shared_domains),'curated':False,'recommended_next':'ADAPTER_AND_CONTRASTIVE_BOUNDARY_BENCHMARK'}
    curated=[
      ('SharedCapacityAllocatorV0','P031',25,'Scale EVLT beyond additive audit values while preserving shared-capacity accounting'),
      ('EffectiveDiversityGuardV0','P003',22,'Gate SANP support masks with effective rather than nominal diversity'),
      ('SelectionAwareReferenceLawV0','P137',22,'Protect memory-policy selection with reference-law-aware holdout routing'),
      ('SelectionAwareReferenceLawV0','P142',22,'Protect burnout-model selection against temporal reference-law drift'),
      ('MultiFidelityBudgetControllerV0','P136',21,'Allocate quasineutral measurements across fidelity and cost'),
      ('MultiFidelityBudgetControllerV0','P144',21,'Route persistence-identification experiments by fidelity budget'),
      ('DecisionSufficientCompressorV0','P002',20,'Add decision-sufficiency diagnostics to predictive closure refinement'),
      ('SafeProblemReducerV0','P143',20,'Reduce liquidity allocation only when integrality meaning survives'),
      ('AdmissibleShiftRobustOptimizerV0','P025',20,'Route identification envelopes across declared shift regions'),
      ('ConstraintPressureMonitorV0','P026',19,'Use constraint pressure to target deployable bottleneck scans'),
      ('ObservationPolicyConfoundingGuardV0','P138',19,'Prevent search-policy acquisition from learning its own observation bias'),
      ('GuaranteeTransportGateV0','P135',18,'Prevent deletion certificates from escaping their sensing shell'),
    ]
    for lcb_name,pid,boost,note in curated:
        supplier=lcb_by_name.get(lcb_name); consumer='FOUNDRY:'+pid
        if not supplier or consumer not in profiles:continue
        key=(supplier,consumer); base=candidates.get(key,{'supplier_id':supplier,'consumer_id':consumer,'score':0,'interface_matches':[],'addressed_weaknesses':[],'shared_domains':[],'recommended_next':'ADAPTER_AND_CONTRASTIVE_BOUNDARY_BENCHMARK'})
        base['score']+=boost+30; base['curated']=True; base['curated_rationale']=note; candidates[key]=base
    adjudications={}
    if ADJUDICATIONS.exists():
        for line in ADJUDICATIONS.read_text(encoding='utf-8').splitlines():
            if not line.strip(): continue
            a=json.loads(line); adjudications[(a['supplier_id'],a['consumer_id'])]=a
    for key,row in candidates.items():
        a=adjudications.get(key)
        if a is None:
            row.setdefault('adjudication_state','UNADJUDICATED')
            row.setdefault('active_for_build',True)
            continue
        row['adjudication_state']=a.get('adjudication_state','ADJUDICATED')
        row['active_for_build']=bool(a.get('active_for_build',True))
        row['adjudication_reason']=a.get('reason')
        row['adjudication_generation']=a.get('adjudication_generation')
        row['adjudication_scope']=a.get('scope')
        row['adjudication_does_not_imply']=a.get('does_not_imply')
        if not row['active_for_build']:
            row['recommended_next']='HOLD_REJECTED_INTERFACE_NO_BUILD'
    ranked=sorted(candidates.values(),key=lambda r:(0 if r.get('active_for_build',True) else 1,-r['score'],r['supplier_id'],r['consumer_id']))
    # R5 experiment-routing + telemetry schema. Values remain explicitly UNKNOWN until a
    # research decision and calibrated test contract are declared; the builder
    # never manufactures information gain or compute estimates from prose.
    # R6 additionally marks the small subset of queue edges that already have an
    # exact completed V2 composition with a fixed executable suite.  This is only
    # bootstrap readiness: it does not fabricate numeric routing fields.
    from experiment_contract_bootstrap import discover_existing_composition_suites, discover_foundry_component_test_surfaces
    from telemetry_registry import write_registry, hydrate_queue_row
    bootstrap_suites=discover_existing_composition_suites(ROOT)
    component_test_surfaces=discover_foundry_component_test_surfaces(ROOT)
    # R12 canonicalizes all versioned experiment telemetry before queue hydration.
    # This is organizational/calibration state only; it does not promote scientific evidence.
    _,_,telemetry_index=write_registry(ROOT)
    for row in ranked:
        row.setdefault('decision_id', None)
        row.setdefault('uncertainty_axes', None)
        row.setdefault('test_channels', None)
        row.setdefault('experiment_routing_status', 'NOT_READY_MISSING_DECLARED_CONTRACT')
        row.setdefault('experiment_telemetry_status', 'NO_STANDARDIZED_RUNS_RECORDED')
        suite=bootstrap_suites.get((row['supplier_id'],row['consumer_id']))
        if suite is not None:
            row['experiment_bootstrap_status']='FIXED_PILOT_SCHEDULE_AVAILABLE'
            row['experiment_bootstrap_product_id']=suite.product_id
            row['experiment_bootstrap_case_count']=len(suite.cases)
            row['experiment_bootstrap_problem_shell']=suite.problem_shell
        elif row['consumer_id'] in component_test_surfaces:
            surf=component_test_surfaces[row['consumer_id']]
            row['experiment_bootstrap_status']='ADAPTER_REQUIRED_CONSUMER_INVARIANT_SUITE_AVAILABLE'
            row['experiment_bootstrap_product_id']=surf.product_id
            row['experiment_bootstrap_case_count']=surf.case_count
            row['experiment_bootstrap_problem_shell']=None
        elif row['supplier_id'] in component_test_surfaces:
            surf=component_test_surfaces[row['supplier_id']]
            row['experiment_bootstrap_status']='SUPPLIER_INVARIANT_SUITE_AVAILABLE_NO_COMPOSITION_HARNESS'
            row['experiment_bootstrap_product_id']=surf.product_id
            row['experiment_bootstrap_case_count']=surf.case_count
            row['experiment_bootstrap_problem_shell']=None
        else:
            row['experiment_bootstrap_status']='NO_EXECUTABLE_TEST_SURFACE_DISCOVERED'
            row['experiment_bootstrap_product_id']=None
            row['experiment_bootstrap_case_count']=None
            row['experiment_bootstrap_problem_shell']=None
        hydrated=hydrate_queue_row(row,telemetry_index)
        row.clear(); row.update(hydrated)
    (OUT/'CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    rejected=[r for r in ranked if not r.get('active_for_build',True)]
    active=[r for r in ranked if r.get('active_for_build',True)]
    # R388 completeness: persist the full ranked candidate universe.  The top-1000
    # composition queue is an operational priority window, not the ontology/graph
    # boundary.  Candidates below that window must remain visible and addressable.
    active_rank=0
    for global_rank,row in enumerate(ranked,1):
        row['candidate_universe_rank']=global_rank
        if row.get('active_for_build',True):
            active_rank+=1
            row['active_candidate_rank']=active_rank
        else:
            row['active_candidate_rank']=None
    universe_path=OUT/'CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl'
    universe_path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in ranked),encoding='utf-8')
    (OUT/'CORE_V2_FOUNDRY_REJECTED_EDGES.json').write_text(json.dumps(rejected,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # The operational queue is bounded, but it must never evict already-completed
    # composition suites or explicit curated hypotheses merely because newly visible
    # candidates outrank them. Fill the remaining slots from native active rank.
    pinned=[r for r in active if r.get('experiment_bootstrap_status')=='FIXED_PILOT_SCHEDULE_AVAILABLE' or bool(r.get('curated'))]
    pinned_keys={(r['supplier_id'],r['consumer_id']) for r in pinned}
    queue_rows=list(pinned)
    for r in active:
        if len(queue_rows)>=1000: break
        if (r['supplier_id'],r['consumer_id']) in pinned_keys: continue
        queue_rows.append(r)
    queue_rows.sort(key=lambda r:r['active_candidate_rank'])
    for i,row in enumerate(queue_rows,1): row['operational_queue_rank']=i
    (OUT/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').write_text(json.dumps(queue_rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (OUT/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.tsv').open('w',encoding='utf-8',newline='') as f:
        fields=['rank','supplier_id','consumer_id','score','curated','active_for_build','adjudication_state','interface_matches','addressed_weaknesses','shared_domains','recommended_next','curated_rationale','decision_id','experiment_routing_status']; w=csv.DictWriter(f,fields,delimiter='\t',extrasaction='ignore');w.writeheader()
        for i,row in enumerate(queue_rows,1):w.writerow({'rank':i,**row,'interface_matches':','.join(row['interface_matches']),'addressed_weaknesses':','.join(row['addressed_weaknesses']),'shared_domains':','.join(row['shared_domains'])})
    counts={'records':len(records),'families':dict(Counter(r['family'] for r in records)),'evidence_tiers':dict(Counter(r['evidence_tier'] for r in records)),'candidate_edges':len(candidates),'candidate_universe_rows':len(ranked),'active_candidate_rows':len(active),'queue_rows':len(queue_rows),'queue_pinned_rows':len(pinned),'queue_completed_suite_rows':sum(r.get('experiment_bootstrap_status')=='FIXED_PILOT_SCHEDULE_AVAILABLE' for r in queue_rows),'curated_edges':sum(r.get('curated',False) for r in candidates.values()),'rejected_current_interface_edges':sum(not r.get('active_for_build',True) for r in candidates.values()),'standardized_telemetry_events':telemetry_index.get('event_count',0),'calibrated_completed_suites':telemetry_index.get('calibrated_current_suite_count',0)}
    (OUT/'CORE_V2_FOUNDRY_COUNTS.json').write_text(json.dumps(counts,indent=2)+'\n',encoding='utf-8')
    top='\n'.join(f"{i}. `{r['supplier_id']}` → `{r['consumer_id']}` — score {r['score']:.1f}"+(f" — {r.get('curated_rationale')}" if r.get('curated') else '')+(" — REJECTED_CURRENT_INTERFACE" if not r.get('active_for_build',True) else '') for i,r in enumerate(active[:25],1))
    (OUT/'CURRENT_V2_FOUNDRY_FRONTIER.md').write_text(f'# Core V2 + Foundry frontier\n\nUnified records: **{len(records)}**. Directed Foundry-inclusive candidate edges: **{len(candidates)}**. Full ranked candidate universe is persisted in `CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl`; the JSON/TSV composition queue remains the top-1000 operational priority window only.\n\n## Top queue\n\n{top}\n\nNegative evidence remains shell-local; queue rank prioritizes builds and does not kill or hide lower-ranked capabilities.\n',encoding='utf-8')
    print(json.dumps(counts,indent=2)); print('top',active[0]); print('rejected_edges',len(rejected))


if __name__=='__main__':main()
