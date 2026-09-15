from __future__ import annotations
import argparse,json
from pathlib import Path
from core_v2 import bootstrap_foundry_experiment_contract
from experiment_contract_bootstrap import run_fixed_suite_pilot,compile_bootstrap_and_route


def main():
    ap=argparse.ArgumentParser(description='Bootstrap a non-fabricated experiment contract from an existing Lab composition suite.')
    ap.add_argument('supplier_id'); ap.add_argument('consumer_id')
    ap.add_argument('--search-generation',type=int,default=0)
    ap.add_argument('--run-fixed-pilot',action='store_true')
    ap.add_argument('--record-ledger',type=Path,help='Append pilot telemetry to this JSONL ledger; requires --event-namespace')
    ap.add_argument('--event-namespace',help='Unique namespace for recorded event IDs')
    args=ap.parse_args()
    draft=bootstrap_foundry_experiment_contract(args.supplier_id,args.consumer_id,search_generation=args.search_generation)
    out={'draft':draft.to_dict()}
    if args.run_fixed_pilot:
        if args.record_ledger is not None and not args.event_namespace:
            raise SystemExit('--event-namespace is required with --record-ledger')
        events=run_fixed_suite_pilot(draft,release_generation=args.search_generation+1,event_namespace=(args.event_namespace or 'UNRECORDED_PILOT'))
        future,hydrated,snapshot,plan=compile_bootstrap_and_route(draft,events,target_generation=args.search_generation+2)
        out['pilot_events']=[e.to_dict() for e in events]
        out['calibration_snapshot']=snapshot.to_dict()
        out['future_plan']=plan.to_dict()
        if args.record_ledger is not None:
            from experiment_telemetry import ExperimentTelemetryLedger
            ledger=ExperimentTelemetryLedger.load_jsonl(args.record_ledger)
            for event in events:
                ledger.append_jsonl(args.record_ledger,event)
            out['recorded_telemetry_ledger']=str(args.record_ledger)
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
