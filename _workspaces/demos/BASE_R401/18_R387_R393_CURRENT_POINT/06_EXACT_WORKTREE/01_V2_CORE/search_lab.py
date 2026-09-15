"""CLI for persistent LabAllCompass search sessions."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from core_v2 import build_search_router
from lab_search_engine import SearchQuery


def render(result,state_restore=None):
    return {
        'status':result.status,'documents_total':result.documents_total,'documents_eligible':result.documents_eligible,
        'query_features_changed':result.query_features_changed,'documents_affected_by_delta':result.documents_affected_by_delta,
        'exact_rescored_this_update':result.exact_rescored_this_update,'exact_score_computations_total':result.exact_score_computations_total,
        'reused_without_rescore':result.reused_without_rescore,'competitive_frontier_size':result.competitive_frontier_size,
        'state_restore':state_restore,
        'hits':[{'rank':i,'document_id':h.document_id,'name':h.name,'family':h.family,'score':round(h.score,6),
                 'score_lower':round(h.score_lower,6),'score_upper':round(h.score_upper,6),
                 'exact_for_current_query':h.exact_for_current_query,'metadata':h.metadata}
                for i,h in enumerate(result.hits,1)],
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--query',type=Path,required=True,help='JSON problem/search contract')
    ap.add_argument('--mode',choices=['capabilities','primitives','suppliers'],default='capabilities')
    ap.add_argument('--consumer-id',default=None,help='required for --mode suppliers')
    ap.add_argument('--top-k',type=int,default=None)
    ap.add_argument('--state-in',type=Path,default=None,help='optional prior router snapshot')
    ap.add_argument('--state-out',type=Path,default=None,help='write updated router snapshot')
    ap.add_argument('--output',type=Path,default=None)
    args=ap.parse_args()
    obj=json.loads(args.query.read_text(encoding='utf-8'))
    top_k=int(args.top_k if args.top_k is not None else obj.get('top_k',obj.get('candidate_limit',20)))
    router=build_search_router(); restore=None
    if args.state_in and args.state_in.exists(): restore=router.load_snapshot(args.state_in)
    if args.mode=='suppliers':
        if not args.consumer_id: ap.error('--consumer-id is required for supplier search')
        objective=' '.join(str(obj.get(k,'')) for k in ('objective','diagnosed_failure','mechanism_needs','text','query'))
        result=router.search_suppliers(args.consumer_id,objective,top_k=top_k,incremental=True)
    else:
        q=SearchQuery.from_dict(obj,top_k=top_k)
        result=router.search_capabilities(q,incremental=True) if args.mode=='capabilities' else router.discover_primitives(q,incremental=True)
    if args.state_out:
        args.state_out.parent.mkdir(parents=True,exist_ok=True); router.save_snapshot(args.state_out)
    text=json.dumps(render(result,restore),indent=2,ensure_ascii=False)+'\n'
    if args.output: args.output.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
