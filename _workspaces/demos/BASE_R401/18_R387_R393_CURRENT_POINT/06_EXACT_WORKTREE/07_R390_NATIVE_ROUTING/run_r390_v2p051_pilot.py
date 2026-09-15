from __future__ import annotations
import json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CORE=ROOT/'01_V2_CORE'; sys.path.insert(0,str(CORE))
from experiment_contract_bootstrap import discover_existing_composition_suites,bootstrap_queue_row,run_fixed_suite_pilot
from experiment_telemetry import ExperimentTelemetryLedger
from telemetry_registry import save_ledger
PAIR=('PARENT:R037_SUPPORT_COVARIANCE_SACPS','PARENT:R044_DECISION_LOSS_DLEW'); PID='V2P051'
ledger_path=CORE/'search_data/EXPERIMENT_TELEMETRY.jsonl'; queue_path=CORE/'generated_v2_foundry/CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
old=ExperimentTelemetryLedger.load_jsonl(ledger_path)
# Fail closed if this namespace already exists; reruns must not manufacture duplicate evidence.
if any(e.event_id.startswith('R390::V2P051::') for e in old.events): raise RuntimeError('R390 V2P051 pilot already present')
suite=discover_existing_composition_suites(CORE).get(PAIR)
if suite is None or suite.product_id!=PID: raise RuntimeError(f'current exact suite missing: {suite}')
row=next((r for r in json.loads(queue_path.read_text()) if (str(r['supplier_id']),str(r['consumer_id']))==PAIR),None)
if row is None: raise RuntimeError('pair absent from operational queue')
draft=bootstrap_queue_row(row,root=CORE,search_generation=390)
if draft.suite is None or draft.suite.product_id!=PID: raise RuntimeError('bootstrap did not resolve V2P051')
events=run_fixed_suite_pilot(draft,release_generation=390,timeout_seconds=60.,event_namespace='R390')
if len(events)!=len(suite.cases) or any(e.run_status!='COMPLETE' or not e.measurement_valid for e in events): raise RuntimeError('pilot not fully complete')
merged=ExperimentTelemetryLedger(sorted(tuple(old.events)+tuple(events),key=lambda e:e.event_id))
tmp=ledger_path.with_suffix('.r390.tmp'); save_ledger(tmp,merged); os.replace(tmp,ledger_path)
receipt={'release':'R390','product_id':PID,'pair':list(PAIR),'events_added':len(events),'old_event_count':len(old.events),'new_event_count':len(merged.events),'statuses':{s:sum(e.run_status==s for e in events) for s in ('COMPLETE','FAILED','CENSORED')},'test_signature':suite.test_signature,'problem_shell':suite.problem_shell,'cases':list(suite.cases),'evidence_boundary':'mechanics/executable-contract calibration only; not empirical validation'}
(ROOT/'07_R390_NATIVE_ROUTING/R390_V2P051_RAPID_PILOT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,indent=2))
