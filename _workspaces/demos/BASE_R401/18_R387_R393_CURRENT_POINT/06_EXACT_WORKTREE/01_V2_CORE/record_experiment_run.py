"""Append one standardized experiment-run record to the canonical R12 telemetry ledger.

This is a thin validated writer. It does not infer uncertainty, calibration
eligibility, backreaction, evidence role, or scientific success from arbitrary
experiment output. Those fields must be supplied by the experiment contract/run.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from experiment_telemetry import ExperimentRunRecord, ExperimentTelemetryLedger

ROOT=Path(__file__).resolve().parent
DEFAULT_LEDGER=ROOT/'search_data'/'EXPERIMENT_TELEMETRY.jsonl'

def main():
    ap=argparse.ArgumentParser(description='Append one explicit ExperimentRunRecord; optionally refresh Lab state.')
    ap.add_argument('--json',type=Path,required=True,help='ExperimentRunRecord JSON object')
    ap.add_argument('--ledger',type=Path,default=DEFAULT_LEDGER)
    ap.add_argument('--no-refresh',action='store_true')
    args=ap.parse_args()
    obj=json.loads(args.json.read_text(encoding='utf-8'))
    event=ExperimentRunRecord.from_dict(obj)
    ExperimentTelemetryLedger().append_jsonl(args.ledger,event)
    if not args.no_refresh and args.ledger.resolve()==DEFAULT_LEDGER.resolve():
        subprocess.run([sys.executable,str(ROOT/'refresh_lab_state.py')],cwd=ROOT,check=True)
    print(json.dumps({'recorded_event_id':event.event_id,'ledger':str(args.ledger),'refreshed':not args.no_refresh and args.ledger.resolve()==DEFAULT_LEDGER.resolve()},indent=2))

if __name__=='__main__': main()
