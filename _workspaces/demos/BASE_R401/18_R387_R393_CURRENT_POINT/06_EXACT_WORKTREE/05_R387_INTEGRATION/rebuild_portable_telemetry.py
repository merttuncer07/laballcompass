from __future__ import annotations
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / '01_V2_CORE'
sys.path.insert(0, str(CORE))

from experiment_contract_bootstrap import discover_existing_composition_suites, bootstrap_queue_row, run_fixed_suite_pilot
from experiment_telemetry import ExperimentTelemetryLedger
from telemetry_registry import save_ledger

CHANGED = {'V2P040','V2P041','V2P042','V2P043','V2P044','V2P045','V2P046','V2P048'}
LEDGER = CORE / 'search_data' / 'EXPERIMENT_TELEMETRY.jsonl'
QUEUE = CORE / 'generated_v2_foundry' / 'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
OUT = ROOT / '05_R387_INTEGRATION'

def product_id(event):
    for tag in event.shell_tags:
        if tag.startswith('V2P') and tag[4:].isdigit():
            return tag
    if event.test_id.startswith('BOOTSTRAP_UNIT_CASE::V2P'):
        return event.test_id.split('::')[-1]
    return None

def main():
    old = ExperimentTelemetryLedger.load_jsonl(LEDGER)
    superseded = [e for e in old.events if product_id(e) in CHANGED]
    retained = [e for e in old.events if product_id(e) not in CHANGED]
    save_ledger(OUT / 'R386_SUPERSEDED_ABSOLUTE_PATH_TELEMETRY.jsonl', ExperimentTelemetryLedger(superseded))
    save_ledger(OUT / 'R387_RETAINED_TELEMETRY_BASE.jsonl', ExperimentTelemetryLedger(retained))

    suites = discover_existing_composition_suites(CORE)
    by_pid = {s.product_id:(pair,s) for pair,s in suites.items()}
    missing = CHANGED - set(by_pid)
    if missing:
        raise RuntimeError(f'missing current suites: {sorted(missing)}')
    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    by_pair = {(str(r['supplier_id']),str(r['consumer_id'])):r for r in queue}

    fresh=[]; per_product=[]
    for pid in sorted(CHANGED):
        pair,suite = by_pid[pid]
        row = by_pair.get(pair)
        if row is None:
            raise RuntimeError(f'{pid}: pair not in native queue: {pair}')
        draft = bootstrap_queue_row(row, root=CORE, search_generation=387)
        if draft.suite is None or draft.suite.product_id != pid:
            raise RuntimeError(f'{pid}: wrong bootstrap suite: {None if draft.suite is None else draft.suite.product_id}')
        events = run_fixed_suite_pilot(draft, release_generation=387, timeout_seconds=60.0, event_namespace='R387_PORTABLE')
        statuses={}
        for e in events: statuses[e.run_status]=statuses.get(e.run_status,0)+1
        per_product.append({'product_id':pid,'pair':list(pair),'cases':len(events),'statuses':statuses,'test_signature':suite.test_signature,'problem_shell':suite.problem_shell})
        if len(events) != len(suite.cases) or any(e.run_status!='COMPLETE' or not e.measurement_valid for e in events):
            (OUT/'R387_PORTABLE_TELEMETRY_ABORT.json').write_text(json.dumps({'product':pid,'per_product':per_product},indent=2)+'\n')
            raise RuntimeError(f'{pid}: pilot not fully COMPLETE')
        fresh.extend(events)

    fresh_ledger=ExperimentTelemetryLedger(fresh)
    save_ledger(OUT/'R387_PORTABLE_TELEMETRY_EVENTS.jsonl',fresh_ledger)
    merged=ExperimentTelemetryLedger(sorted(retained+fresh,key=lambda e:e.event_id))
    tmp=LEDGER.with_suffix('.r387.tmp')
    save_ledger(tmp,merged)
    os.replace(tmp,LEDGER)
    summary={
        'model_version':'R387_PORTABLE_TELEMETRY_REBUILD_V1',
        'old_event_count':len(old.events),
        'superseded_event_count':len(superseded),
        'retained_event_count':len(retained),
        'fresh_event_count':len(fresh),
        'new_event_count':len(merged.events),
        'changed_products':sorted(CHANGED),
        'per_product':per_product,
        'policy':[
            'R386 telemetry tied to pre-portability exact suite fingerprints is preserved separately, not treated as current calibration.',
            'R387 current ledger keeps unaffected exact-match telemetry and replaces only superseded exact-shell events for modified suites.',
            'These are mechanics/channel calibration events, not empirical or scientific validation.'
        ]
    }
    (OUT/'R387_PORTABLE_TELEMETRY_REBUILD_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
