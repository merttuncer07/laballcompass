"""Canonical telemetry registry for LabAllCompass R12.

R5-R11 already produced valid standardized experiment events. R12 closes the
operational loop by making one canonical ledger/index/calibration registry and by
hydrating the factory queue from it.

No new scientific evidence is manufactured here. This module organizes recorded
telemetry and calibrates executable test channels only under the existing
exact-shell/exact-signature/generation rules.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping
import hashlib, json, re

from experiment_telemetry import ExperimentRunRecord, ExperimentTelemetryLedger, compile_calibration_snapshot
from experiment_contract_bootstrap import discover_existing_composition_suites

MODEL_VERSION="LAB_TELEMETRY_REGISTRY_R12_V1"


def _edge_from_decision(decision_id: str) -> tuple[str,str] | None:
    m=re.fullmatch(r"COMPOSITION::(.+?)->(.+)", decision_id)
    return (m.group(1),m.group(2)) if m else None


def _product_from_event(e: ExperimentRunRecord) -> str | None:
    for tag in e.shell_tags:
        if re.fullmatch(r"V2P\d+",tag): return tag
    m=re.search(r"::(V2P\d+)$",e.test_id)
    return m.group(1) if m else None


def merge_ledgers(paths: Iterable[str|Path]) -> ExperimentTelemetryLedger:
    by_id: dict[str,ExperimentRunRecord]={}
    for path in paths:
        p=Path(path)
        if not p.exists(): continue
        for e in ExperimentTelemetryLedger.load_jsonl(p).events:
            old=by_id.get(e.event_id)
            if old is not None and old.to_dict()!=e.to_dict():
                raise ValueError(f"conflicting telemetry event_id: {e.event_id}")
            by_id[e.event_id]=e
    return ExperimentTelemetryLedger(by_id[k] for k in sorted(by_id))


def save_ledger(path: str|Path, ledger: ExperimentTelemetryLedger) -> None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(''.join(json.dumps(e.to_dict(),sort_keys=True,ensure_ascii=False)+'\n' for e in ledger.events),encoding='utf-8')


def build_telemetry_index(core_root: str|Path, ledger: ExperimentTelemetryLedger) -> dict:
    core=Path(core_root).resolve()
    suites=discover_existing_composition_suites(core)
    suite_by_triplet={(s.test_id,s.test_signature,s.problem_shell):s for s in suites.values()}
    by_edge={}; by_product={}; by_shell={}; by_test={}; roles={}; statuses={}; generations={}
    exact_suite_matches=0; unmatched=[]
    for e in ledger.events:
        edge=_edge_from_decision(e.decision_id)
        edge_key=None if edge is None else f"{edge[0]}->{edge[1]}"
        prod=_product_from_event(e)
        suite=suite_by_triplet.get((e.test_id,e.test_signature,e.problem_shell))
        if suite is not None: exact_suite_matches+=1
        else: unmatched.append(e.event_id)
        def bump(d,k,sub=None):
            if k is None:return
            row=d.setdefault(k,{"event_count":0,"complete":0,"failed":0,"censored":0,"usable_measurements":0})
            row["event_count"]+=1
            row[e.run_status.lower()]+=1
            if e.usable_measurement: row["usable_measurements"]+=1
            if sub:
                for sk,sv in sub.items(): row[sk]=sv
        bump(by_edge,edge_key,{"supplier_id":edge[0],"consumer_id":edge[1]} if edge else None)
        bump(by_product,prod)
        bump(by_shell,e.problem_shell)
        bump(by_test,e.test_id,{"signatures":sorted(set(by_test.get(e.test_id,{}).get("signatures",[]))|{e.test_signature})})
        roles[e.evidence_role.value]=roles.get(e.evidence_role.value,0)+1
        statuses[e.run_status]=statuses.get(e.run_status,0)+1
        generations[str(e.search_generation)]=generations.get(str(e.search_generation),0)+1
    calibration={}
    # Calibrate each current executable composition suite for the next safe generation.
    target_generation=max([e.release_generation for e in ledger.events],default=0)+1
    for pair,s in sorted(suites.items()):
        snap=compile_calibration_snapshot(ledger.events,target_generation=target_generation,problem_shell=s.problem_shell)
        cal=snap.lookup(s.test_id,s.test_signature)
        edge_key=f"{pair[0]}->{pair[1]}"
        if cal is None:
            calibration[edge_key]={"status":"NO_EXACT_CALIBRATION","product_id":s.product_id,"problem_shell":s.problem_shell,"test_signature":s.test_signature}
            continue
        axis_ready=bool(cal.expected_resolution_lower_by_axis) and all(v is not None for v in cal.expected_resolution_lower_by_axis.values())
        ready=cal.reliability_lower_bound is not None and cal.compute_upper_seconds is not None and axis_ready
        calibration[edge_key]={
            "status":"CALIBRATED_EXACT_SHELL" if ready else "INSUFFICIENT_SUPPORT",
            "product_id":s.product_id,"problem_shell":s.problem_shell,"test_id":s.test_id,"test_signature":s.test_signature,
            "attempt_count":cal.attempt_count,"usable_count":cal.usable_count,
            "reliability_lower_bound":cal.reliability_lower_bound,"compute_upper_seconds":cal.compute_upper_seconds,
            "expected_resolution_lower_by_axis":dict(cal.expected_resolution_lower_by_axis),
            "calibration_id":cal.calibration_id,"target_generation":target_generation,
        }
    payload={
        "model_version":MODEL_VERSION,
        "event_count":len(ledger.events),
        "unique_event_ids":len({e.event_id for e in ledger.events}),
        "exact_current_suite_matches":exact_suite_matches,
        "unmatched_event_count":len(unmatched),
        "unmatched_event_ids":unmatched,
        "evidence_roles":roles,"run_statuses":statuses,"search_generations":generations,
        "by_edge":by_edge,"by_product":by_product,"by_shell":by_shell,"by_test":by_test,
        "calibration_by_edge":calibration,
        "current_completed_suite_count":len(suites),
        "calibrated_current_suite_count":sum(1 for x in calibration.values() if x["status"]=="CALIBRATED_EXACT_SHELL"),
        "policy":{
            "telemetry_is_not_scientific_validation":True,
            "exact_shell_and_signature_only":True,
            "protected_validation_never_calibrates_adaptive_routing":True,
            "unknown_stays_unknown":True,
        },
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    payload["fingerprint"]=hashlib.sha256(raw).hexdigest()
    return payload


def write_registry(core_root: str|Path, *, source_ledgers: Iterable[str|Path] | None=None) -> tuple[Path,Path,dict]:
    core=Path(core_root).resolve()
    ledger_path=core/"search_data"/"EXPERIMENT_TELEMETRY.jsonl"
    if source_ledgers is None:
        # Historical bootstrap fragments remain provenance sources, but the canonical
        # ledger is also an input so mission/runtime events appended after R12 survive
        # every refresh. Exact duplicate IDs deduplicate; conflicting payloads fail.
        fragments=sorted((core/"generated_search").glob("EXPERIMENT_TELEMETRY_BOOTSTRAP_R*.jsonl"))
        source_ledgers=([ledger_path] if ledger_path.exists() else []) + fragments
    ledger=merge_ledgers(source_ledgers)
    index_path=core/"generated_search"/"EXPERIMENT_TELEMETRY_INDEX_R12.json"
    save_ledger(ledger_path,ledger)
    index=build_telemetry_index(core,ledger)
    index_path.write_text(json.dumps(index,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    return ledger_path,index_path,index


def hydrate_queue_row(row: Mapping[str,object], index: Mapping[str,object]) -> dict:
    out=dict(row)
    edge_key=f"{out.get('supplier_id')}->{out.get('consumer_id')}"
    ev=dict(index.get("by_edge",{})).get(edge_key)
    cal=dict(index.get("calibration_by_edge",{})).get(edge_key)
    if ev:
        out["experiment_telemetry_status"]="STANDARDIZED_TELEMETRY_AVAILABLE"
        out["experiment_telemetry_event_count"]=int(ev.get("event_count",0))
        out["experiment_telemetry_complete_count"]=int(ev.get("complete",0))
        out["experiment_telemetry_usable_count"]=int(ev.get("usable_measurements",0))
    else:
        out["experiment_telemetry_status"]="NO_STANDARDIZED_RUNS_RECORDED"
        out["experiment_telemetry_event_count"]=0
        out["experiment_telemetry_complete_count"]=0
        out["experiment_telemetry_usable_count"]=0
    if cal:
        out["experiment_calibration_status"]=cal.get("status")
        out["experiment_calibration_id"]=cal.get("calibration_id")
        out["experiment_calibration_target_generation"]=cal.get("target_generation")
        if cal.get("status")=="CALIBRATED_EXACT_SHELL" and out.get("experiment_routing_status")=="NOT_READY_MISSING_DECLARED_CONTRACT":
            out["experiment_routing_status"]="BOOTSTRAP_CHANNEL_CALIBRATED_SCIENTIFIC_CONTRACT_STILL_REQUIRED"
    else:
        out["experiment_calibration_status"]="NO_EXACT_CALIBRATION"
        out["experiment_calibration_id"]=None
        out["experiment_calibration_target_generation"]=None
    return out
