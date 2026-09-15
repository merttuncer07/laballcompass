from __future__ import annotations
import collections, json, math, signal, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
LAB=HERE.parent
CORE=LAB/'01_V2_CORE'
R388=LAB/'05_R388_NATIVE_ROUTING'
sys.path.insert(0,str(CORE))
from core_v2 import build_search_router
from lab_search_engine import SearchQuery

BOUND=R388/'R77_BOUNDARY_SENTENCES_SOURCE.json'
CANDS=HERE/'R392_FULL_FRESH_ADJUDICATION_QUEUE.jsonl'

class TO(Exception): pass
def handler(s,f): raise TO()
signal.signal(signal.SIGALRM,handler)

def load_jsonl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def main():
    rows=json.loads(BOUND.read_text())
    cands=load_jsonl(CANDS)
    router=build_search_router()
    cap_score=collections.Counter(); cap_rank_hits=collections.Counter(); cap_cats=collections.defaultdict(collections.Counter)
    boundary_hits=[]; errors=[]; start=time.time()
    for i,r in enumerate(rows):
        q=SearchQuery.from_dict({'objective':r['text'],'diagnosed_failure':' '.join(r.get('categories',[])),'mechanism_needs':r.get('categories',[]),'query':r['text']},top_k=12)
        try:
            signal.alarm(3)
            res=router.search_capabilities(q,incremental=False)
            signal.alarm(0)
            hs=[]
            for rank,h in enumerate(res.hits[:12],1):
                w=13-rank
                cap_score[h.document_id]+=w*max(float(h.score),0.1)
                cap_rank_hits[h.document_id]+=w
                for cat in r.get('categories',[]): cap_cats[h.document_id][cat]+=1
                hs.append({'id':h.document_id,'name':h.name,'rank':rank,'score':h.score})
            boundary_hits.append({'index':i,'product_dir':r['product_dir'],'categories':r.get('categories',[]),'text':r['text'],'hits':hs})
        except Exception as ex:
            signal.alarm(0); errors.append({'index':i,'error':repr(ex),'row':r})
    scored=[]
    for e in cands:
        s,c=e['supplier_id'],e['consumer_id']
        rs=cap_score.get(s,0.0); rc=cap_score.get(c,0.0)
        hs=cap_rank_hits.get(s,0); hc=cap_rank_hits.get(c,0)
        cats=cap_cats.get(s,collections.Counter())+cap_cats.get(c,collections.Counter())
        category_div=len(cats); native=float(e.get('score') or 0)
        priority=math.log1p(rs+rc)*8 + math.log1p(hs+hc)*4 + min(category_div,6)*1.5 + native*0.15
        row=dict(e)
        row.update({
            'native_score':native,'failure_relevance_score':priority,'endpoint_relevance':rs+rc,
            'rank_hit_mass':hs+hc,'category_diversity':category_div,'category_hits':dict(cats.most_common()),
        })
        scored.append(row)
    scored.sort(key=lambda x:(x['failure_relevance_score'],x['native_score']),reverse=True)
    for i,e in enumerate(scored,1): e['r392_failure_rank']=i
    for e in scored[:500]:
        reps=[]
        for b in boundary_hits:
            ids=[h['id'] for h in b['hits'][:8]]
            if e['supplier_id'] in ids or e['consumer_id'] in ids:
                reps.append({'product_dir':b['product_dir'],'categories':b['categories'],'text':b['text'],'endpoint_rank':min([h['rank'] for h in b['hits'] if h['id'] in (e['supplier_id'],e['consumer_id'])],default=99)})
        reps.sort(key=lambda r:r['endpoint_rank'])
        e['representative_failures']=reps[:8]
    out={
      'summary':{'boundaries':len(rows),'successful_boundary_searches':len(boundary_hits),'errors':len(errors),'fresh_candidate_edges_ranked':len(scored),'elapsed_seconds':time.time()-start},
      'errors':errors,
      'capability_ranking':[{'id':k,'name':router.by_id[k].name if k in router.by_id else k,'score':v,'rank_hit_mass':cap_rank_hits[k],'category_hits':dict(cap_cats[k].most_common())} for k,v in cap_score.most_common(120)],
      'edge_ranking':scored,
      'boundary_hits':boundary_hits,
      'release':'R392',
      'nonclaim':'failure relevance is routing priority only; it is not product novelty or empirical validation',
    }
    (HERE/'R392_FULL_FAILURE_ROUTING.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
    print(json.dumps({'summary':out['summary'],'top_edges':[{
      'rank':e['r392_failure_rank'],'supplier':e['supplier_id'],'consumer':e['consumer_id'],'failure_relevance_score':e['failure_relevance_score'],
      'native_score':e['native_score'],'origin':e.get('visibility_origin'),'interfaces':e['interface_matches'],'addressed':e['addressed_weaknesses'],
      'categories':e['category_hits']} for e in scored[:30]]},indent=2,ensure_ascii=False))
if __name__=='__main__': main()
