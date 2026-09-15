"""Append one typed outcome to the Lab search relevance feedback ledger.

This command never changes a live search snapshot. It only records an event.
The event can influence retrieval later if a future generation compiles a new
snapshot and the event role is LEARN_AFTER_GENERATION.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

from relevance_learning import FeedbackEvent, FeedbackLedger


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--event',type=Path,required=True,help='JSON object matching FeedbackEvent schema')
    ap.add_argument('--ledger',type=Path,required=True)
    args=ap.parse_args()
    event=FeedbackEvent.from_dict(json.loads(args.event.read_text(encoding='utf-8')))
    ledger=FeedbackLedger.load_jsonl(args.ledger)
    ledger.append(event)
    ledger.save_jsonl(args.ledger)
    print(json.dumps({'appended':event.event_id,'ledger_events':len(ledger.events),'role':event.role,'selection_generation':event.selection_generation,'release_generation':event.release_generation}))

if __name__=='__main__': main()
