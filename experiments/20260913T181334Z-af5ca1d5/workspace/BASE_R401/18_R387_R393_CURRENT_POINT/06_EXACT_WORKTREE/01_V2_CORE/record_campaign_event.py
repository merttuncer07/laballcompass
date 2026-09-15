from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from campaign_memory import CampaignEvent,append_event

ROOT=Path(__file__).resolve().parent
DEFAULT_LEDGER=ROOT/'search_data'/'CAMPAIGN_MEMORY.jsonl'

def main():
    ap=argparse.ArgumentParser(description='Append one explicit campaign outcome. Refresh Lab state afterwards to sync eligible relevance feedback.')
    ap.add_argument('--json',type=Path,required=True,help='CampaignEvent JSON object')
    ap.add_argument('--ledger',type=Path,default=DEFAULT_LEDGER)
    ap.add_argument('--no-refresh',action='store_true')
    args=ap.parse_args()
    obj=json.loads(args.json.read_text(encoding='utf-8'))
    event=CampaignEvent.from_dict(obj)
    append_event(args.ledger,event)
    refreshed=False
    if not args.no_refresh and args.ledger.resolve()==DEFAULT_LEDGER.resolve():
        subprocess.run([sys.executable,str(ROOT/'refresh_lab_state.py')],cwd=ROOT,check=True)
        refreshed=True
    print(json.dumps({'recorded':event.to_dict(),'ledger':str(args.ledger),'refreshed':refreshed},indent=2,ensure_ascii=False))

if __name__=='__main__': main()
