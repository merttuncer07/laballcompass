"""Compile a frozen leakage-resistant relevance snapshot from the feedback ledger."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from core_v2 import compile_search_relevance_snapshot


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--ledger',type=Path,required=True)
    ap.add_argument('--generation',type=int,required=True)
    ap.add_argument('--problem-shell',required=True)
    ap.add_argument('--shell-tags',nargs='*',default=[])
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    snap=compile_search_relevance_snapshot(args.ledger,target_generation=args.generation,problem_shell=args.problem_shell,shell_tags=args.shell_tags)
    snap.save(args.output)
    print(json.dumps({'fingerprint':snap.fingerprint,'included_events':len(snap.included_event_ids),'quarantined_events':len(snap.quarantined_events),'document_offsets':len(snap.document_offsets),'consumer_specific_offsets':sum(len(v) for v in snap.supplier_offsets_by_consumer.values())}))

if __name__=='__main__': main()
