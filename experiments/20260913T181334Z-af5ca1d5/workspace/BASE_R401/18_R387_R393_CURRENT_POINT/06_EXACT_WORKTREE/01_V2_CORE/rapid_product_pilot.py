"""Parallel fixed-pilot runner for completed V2 product batches.

This is an operational accelerator only. It does not create scientific evidence;
it runs the existing frozen executable-contract cases and appends standardized
mechanics telemetry under the normal exact-shell/signature rules.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse, json

from experiment_contract_bootstrap import bootstrap_queue_row, run_fixed_suite_pilot
from experiment_telemetry import ExperimentTelemetryLedger
from telemetry_registry import save_ledger

ROOT=Path(__file__).resolve().parent


def product_number(product_id:str)->int:
    if not product_id.startswith('V2P') or not product_id[3:].isdigit():
        raise ValueError(product_id)
    return int(product_id[3:])


def run_batch(*,start:int,end:int,search_generation:int,release_generation:int,namespace:str,workers:int=8)->dict:
    queue=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text(encoding='utf-8'))
    rows={(r['supplier_id'],r['consumer_id']):r for r in queue}
    jobs=[]
    for d in sorted((ROOT/'products').glob('V2P*')):
        pid=d.name.split('_',1)[0]
        try:n=product_number(pid)
        except ValueError:continue
        if not start<=n<=end: continue
        meta=d/'COMPOSITION.json'
        if not meta.exists(): continue
        c=json.loads(meta.read_text(encoding='utf-8')); pair=(c['supplier_id'],c['consumer_id'])
        if pair not in rows: raise ValueError(f'{pid} pair absent from queue: {pair}')
        draft=bootstrap_queue_row(rows[pair],root=ROOT,search_generation=search_generation)
        if draft.suite is None or draft.suite.product_id!=pid:
            raise ValueError(f'{pid} suite discovery mismatch')
        jobs.append((pid,draft))

    def one(job):
        pid,draft=job
        return pid,run_fixed_suite_pilot(draft,release_generation=release_generation,event_namespace=namespace)

    events=[]; per_product={}
    with ThreadPoolExecutor(max_workers=max(1,workers)) as pool:
        futs=[pool.submit(one,j) for j in jobs]
        for fut in as_completed(futs):
            pid,ev=fut.result(); events.extend(ev)
            per_product[pid]={'events':len(ev),'complete':sum(e.run_status=='COMPLETE' for e in ev)}

    ledger_path=ROOT/'search_data'/'EXPERIMENT_TELEMETRY.jsonl'
    ledger=ExperimentTelemetryLedger.load_jsonl(ledger_path)
    by_id={e.event_id:e for e in ledger.events}
    added=0
    for e in events:
        old=by_id.get(e.event_id)
        if old is not None and old.to_dict()!=e.to_dict():
            raise ValueError(f'event conflict: {e.event_id}')
        if old is None: added+=1
        by_id[e.event_id]=e
    save_ledger(ledger_path,ExperimentTelemetryLedger(by_id[k] for k in sorted(by_id)))
    return {'products':len(jobs),'events_run':len(events),'events_added':added,'complete':sum(e.run_status=='COMPLETE' for e in events),'per_product':dict(sorted(per_product.items()))}


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--start',type=int,required=True); ap.add_argument('--end',type=int,required=True)
    ap.add_argument('--search-generation',type=int,required=True); ap.add_argument('--release-generation',type=int,required=True)
    ap.add_argument('--namespace',required=True); ap.add_argument('--workers',type=int,default=8)
    a=ap.parse_args()
    print(json.dumps(run_batch(start=a.start,end=a.end,search_generation=a.search_generation,release_generation=a.release_generation,namespace=a.namespace,workers=a.workers),indent=2,sort_keys=True))

if __name__=='__main__': main()
