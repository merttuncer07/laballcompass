from __future__ import annotations
import collections, json, re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HERE=Path(__file__).resolve().parent
LAB=HERE.parent
CORE=LAB/'01_V2_CORE'
ROUTING=json.loads((HERE/'R393_FULL_FAILURE_ROUTING.json').read_text())
CANDS=ROUTING['edge_ranking']

corpus={}
for line in (CORE/'generated_search'/'LAB_SEARCH_CORPUS.jsonl').read_text().splitlines():
    if line.strip():
        r=json.loads(line); corpus[r['document_id']]=r

authority=json.loads((CORE/'CURRENT_PRODUCT_AUTHORITY.json').read_text())
assert authority['authority_release']=='R392', authority.get('authority_release')
canonical=set(authority['canonical_executable_suite_ids'])
quarantined=set(authority.get('quarantined_product_ids',[]))

# Family map is cumulative through the current base authority, not a frozen release subset.
family_by_pid={}
audit_files=[]
v1=CORE/'PRODUCT_QUALITY_AUDIT_V1.json'
if v1.exists(): audit_files.append(v1)
for p in CORE.glob('PRODUCT_QUALITY_AUDIT_R*.json'):
    m=re.fullmatch(r'PRODUCT_QUALITY_AUDIT_R(\d+)\.json',p.name)
    if m and int(m.group(1))<=392:
        audit_files.append(p)
for p in sorted(set(audit_files),key=lambda x:(x.name!='PRODUCT_QUALITY_AUDIT_V1.json',x.name)):
    try: o=json.loads(p.read_text())
    except Exception: continue
    for r in o.get('rows',[]):
        pid=r.get('product_id')
        if pid: family_by_pid[pid]=r.get('family_id') or 'SHADOW_OR_UNMAPPED'

# One collision record per product ID. Core/canonical location wins over stale shadow copies.
products_by_id={}
def read_product_dir(d: Path) -> str:
    chunks=[]
    for p in d.iterdir():
        if p.is_file() and p.suffix in {'.md','.py','.json'} and not p.name.startswith('test_'):
            try: chunks.append(p.read_text(errors='ignore'))
            except Exception: pass
    return '\n'.join(chunks)

for d in sorted((CORE/'products').glob('V2P*')):
    if not d.is_dir(): continue
    pid=d.name.split('_',1)[0]
    products_by_id[pid]={
        'id':pid,'dir':d.name,'text':read_product_dir(d),
        'family':family_by_pid.get(pid,'SHADOW_OR_UNMAPPED'),
        'canonical':pid in canonical,'quarantined':pid in quarantined,
    }

shadow_seen=0
for shadow_root in sorted(LAB.glob('*_NATIVE_ROUTING/SHADOW_PRODUCTS')):
    if not shadow_root.exists(): continue
    for d in sorted(shadow_root.glob('V2P*')):
        if not d.is_dir(): continue
        pid=d.name.split('_',1)[0]
        # Canonical/core copy always wins; stale shadows of already-promoted products are invisible.
        if pid in products_by_id: continue
        shadow_seen += 1
        products_by_id[pid]={
            'id':pid,'dir':str(d.relative_to(LAB)),'text':read_product_dir(d),
            'family':family_by_pid.get(pid,'R393_SHADOW_DISTINCT_CANDIDATE'),
            'canonical':False,'quarantined':False,
        }
products=[products_by_id[k] for k in sorted(products_by_id)]

prepared=[]
for c in CANDS:
    parts=[]
    for eid in (c['supplier_id'],c['consumer_id']):
        r=corpus.get(eid,{})
        parts.append(r.get('text',''))
        parts += list(r.get('strength_tags') or [])+list(r.get('weakness_tags') or [])+list(r.get('input_types') or [])+list(r.get('output_types') or [])
    parts += [' '.join(c.get('shared_domains') or []),' '.join(c.get('addressed_weaknesses') or []),' '.join(c.get('interface_matches') or [])]
    for f in c.get('representative_failures',[])[:8]: parts.append(f.get('text','')+' '+' '.join(f.get('categories') or []))
    x=dict(c); x['_text']='\n'.join(parts); prepared.append(x)

texts=[p['text'] for p in products]+[c['_text'] for c in prepared]
vec=TfidfVectorizer(ngram_range=(1,2),min_df=1,max_df=.985,stop_words='english',sublinear_tf=True,max_features=80000)
M=vec.fit_transform(texts); P=M[:len(products)]; C=M[len(products):]
sim=cosine_similarity(C,P)

stop={'evidence','report','representation','state','gate','action','decision','calibration','support','uncertainty','boundary','transfer','current','product','parent'}
for i,c in enumerate(prepared):
    j=int(sim[i].argmax()); p=products[j]
    c['nearest_product']=p['id']; c['nearest_product_dir']=p['dir']; c['nearest_quality_family']=p['family']; c['nearest_product_is_canonical']=p['canonical']; c['nearest_product_is_quarantined']=p['quarantined']; c['product_collision']=float(sim[i,j])
    tags=[]
    for eid in (c['supplier_id'],c['consumer_id']):
        r=corpus.get(eid,{})
        tags += list(r.get('strength_tags') or [])+list(r.get('weakness_tags') or [])
    tags += list(c.get('addressed_weaknesses') or [])+list(c.get('interface_matches') or [])+list((c.get('category_hits') or {}).keys())
    toks=[]
    for t in tags:
        for z in re.findall(r'[A-Za-z][A-Za-z0-9_-]+',str(t).lower()):
            if len(z)>=4 and z not in stop: toks.append(z)
    c['signature_tokens']=sorted(set(toks))[:28]
    c['opportunity_score']=float(c['failure_relevance_score'])+12*(1-c['product_collision'])+1.5*float(c.get('category_diversity') or 0)+ (2.0 if c.get('new_parent_parent_visibility') else 0.0)

clusters=[]
for c in sorted(prepared,key=lambda z:z['r393_failure_rank']):
    st=set(c['signature_tokens']); assigned=None
    for cl in clusters:
        rt=set(cl['rep']['signature_tokens']); jac=len(st&rt)/max(1,len(st|rt))
        endpoint_same=(c['supplier_id']==cl['rep']['supplier_id'] or c['consumer_id']==cl['rep']['consumer_id'])
        family_same=c['nearest_quality_family']==cl['rep']['nearest_quality_family']
        origin_same=c.get('visibility_origin')==cl['rep'].get('visibility_origin')
        if jac>=0.62 and (endpoint_same or (family_same and origin_same)):
            assigned=cl; break
    if assigned is None:
        clusters.append({'cluster_id':f'R393C{len(clusters)+1:04d}','rep':c,'members':[c]})
    else:
        assigned['members'].append(c)
for cl in clusters:
    cl['size']=len(cl['members']); cl['best_failure_rank']=min(x['r393_failure_rank'] for x in cl['members'])

reps=[cl['rep'] | {'cluster_id':cl['cluster_id'],'cluster_size':cl['size']} for cl in clusters]
remaining=reps.copy(); selected=[]; used_end=collections.Counter(); used_family=collections.Counter(); used_origin=collections.Counter()
while remaining and len(selected)<160:
    best=max(remaining,key=lambda c:c['opportunity_score']-7*used_end[c['supplier_id']]-7*used_end[c['consumer_id']]-5*used_family[c['nearest_quality_family']]-2*used_origin[c.get('visibility_origin')])
    best=dict(best)
    best['diverse_score']=best['opportunity_score']-7*used_end[best['supplier_id']]-7*used_end[best['consumer_id']]-5*used_family[best['nearest_quality_family']]-2*used_origin[best.get('visibility_origin')]
    selected.append(best)
    used_end[best['supplier_id']]+=1; used_end[best['consumer_id']]+=1; used_family[best['nearest_quality_family']]+=1; used_origin[best.get('visibility_origin')]+=1
    remaining=[x for x in remaining if x['cluster_id']!=best['cluster_id']]

summary=[]
for cl in sorted(clusters,key=lambda x:x['best_failure_rank']):
    r=cl['rep']
    summary.append({
      'cluster_id':cl['cluster_id'],'size':cl['size'],'best_failure_rank':cl['best_failure_rank'],
      'supplier_id':r['supplier_id'],'consumer_id':r['consumer_id'],'supplier_name':r['supplier_name'],'consumer_name':r['consumer_name'],
      'failure_relevance_score':r['failure_relevance_score'],'native_score':r['native_score'],'visibility_origin':r.get('visibility_origin'),
      'nearest_product':r['nearest_product'],'nearest_quality_family':r['nearest_quality_family'],'product_collision':r['product_collision'],
      'interface_matches':r['interface_matches'],'addressed_weaknesses':r['addressed_weaknesses'],'category_hits':r['category_hits'],'signature_tokens':r['signature_tokens'],
      'representative_failures':r.get('representative_failures',[]),
      'member_ranks':[x['r393_failure_rank'] for x in cl['members'][:60]],
    })

out={
 'release':'R393','base_authority_release':'R392','edge_count':len(prepared),'cluster_count':len(clusters),
 'product_count_for_collision':len(products),'canonical_products_for_collision':len(canonical),
 'quarantined_products_for_collision':len(quarantined),
 'shadow_products_for_collision':sum(not p['canonical'] and not p['quarantined'] for p in products),
 'shadow_dirs_considered':shadow_seen,'quality_audits_used':[p.name for p in sorted(set(audit_files))],
 'clusters':summary,'diverse_selected':selected,
 'nonclaim':'lexical/mechanism clustering is workload triage only; distinct-family status still requires code-level non-additivity and mechanism-removing control'
}
(HERE/'R393_FULL_CLUSTER_SCREEN.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
print(json.dumps({'edges':len(prepared),'clusters':len(clusters),'products':len(products),'canonical':len(canonical),'shadow':out['shadow_products_for_collision'],'top_diverse':[{ 
 'selection_rank':i+1,'cluster':c['cluster_id'],'supplier':c['supplier_id'],'consumer':c['consumer_id'],'diverse_score':round(c['diverse_score'],3),'failure_rank':c['r393_failure_rank'],'origin':c.get('visibility_origin'),'nearest':c['nearest_product'],'family':c['nearest_quality_family'],'collision':round(c['product_collision'],3),'interfaces':c['interface_matches'],'addressed':c['addressed_weaknesses']} for i,c in enumerate(selected[:50])]},indent=2,ensure_ascii=False))
