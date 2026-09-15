from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent

def h(p):
 x=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): x.update(b)
 return x.hexdigest()

def main():
 e=[]; checked=0
 man=ROOT/'14_INTEGRITY_SHA256.tsv'
 with man.open(encoding='utf-8') as f:
  next(f)
  for line in f:
   rel,exp,size=line.rstrip('\n').split('\t'); p=ROOT/rel; checked+=1
   if not p.exists(): e.append('MISSING '+rel); continue
   if p.stat().st_size!=int(size): e.append('SIZE '+rel)
   if h(p)!=exp: e.append('HASH '+rel)
 s=json.loads((ROOT/'02_CANONICAL_CURRENT_STATE.json').read_text())
 expected={'registry_families':455,'canonical_capabilities':310,'products_executable':52,'quality_distinct_families':39,'telemetry_events':447,'interaction_map_nodes':4310,'interaction_map_edges':16647,'candidate_universe_rows':16594}
 for k,v in expected.items():
  if s.get(k)!=v:e.append(f'{k} expected {v} got {s.get(k)}')
 if s.get('current_product_authority_release')!='R392':e.append('current authority != R392')
 if s.get('quarantined_product_ids')!=['V2P047']:e.append('quarantine != V2P047')
 cp=ROOT/'18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE'
 a=json.loads((cp/'01_V2_CORE/CURRENT_PRODUCT_AUTHORITY.json').read_text())
 if a.get('authority_release')!='R392':e.append('worktree authority != R392')
 if a.get('canonical_executable_suite_count')!=52:e.append('authority products !=52')
 if a.get('canonical_distinct_family_count')!=39:e.append('authority quality !=39')
 if not a.get('registry455_unchanged'):e.append('registry455 mutation flag')
 t=json.loads((cp/'01_V2_CORE/generated_search/EXPERIMENT_TELEMETRY_INDEX_R12.json').read_text())
 for k,v in {'event_count':447,'exact_current_suite_matches':447,'unmatched_event_count':0,'calibrated_current_suite_count':52}.items():
  if t.get(k)!=v:e.append(f'telemetry {k} expected {v} got {t.get(k)}')
 m=json.loads((cp/'01_V2_CORE/generated_search/INTERACTION_MAP_R12.json').read_text())
 if m.get('edge_count')!=16647:e.append('map edges !=16647')
 if m.get('relation_counts')!={'COMPLETED_COMPOSITION':52,'INFERRED_CANDIDATE':16537,'PARENT_OF':53,'REJECTED_CURRENT_INTERFACE':5}:e.append('map relation counts drift')
 v=json.loads((cp/'10_R393_NATIVE_ROUTING/R393_FULL_VISIBILITY_AUDIT.json').read_text())
 c=json.loads((cp/'10_R393_NATIVE_ROUTING/R393_FULL_CLUSTER_SCREEN.json').read_text())
 if v.get('fresh_adjudication_pair_count')!=15578:e.append('R393 fresh !=15578')
 if v.get('candidate_universe_rows')!=16594:e.append('R393 universe !=16594')
 if c.get('cluster_count')!=649:e.append('R393 clusters !=649')
 prods=[p for p in (cp/'01_V2_CORE/products').glob('V2P*') if p.is_dir()]
 if len(prods)!=52:e.append(f'physical canonical product dirs={len(prods)}')
 if any(p.name.startswith('V2P047') for p in prods):e.append('V2P047 incorrectly present in canonical products')
 genealogy=sum(1 for x in (ROOT/'05_ENTITY_GENEALOGY.jsonl').read_text().splitlines() if x.strip())
 if genealogy!=362:e.append(f'genealogy rows={genealogy}')
 maprows=sum(1 for x in (ROOT/'16_INTERACTION_INSTRUMENTATION_MAP.jsonl').read_text().splitlines() if x.strip())
 if maprows!=16647:e.append(f'instrumentation rows={maprows}')
 print(json.dumps({'status':'PASS' if not e else 'FAIL','errors':e,'checked_manifest_files':checked,'historical_base':'R12 / Registry455 / Products38 / Quality28','current_product_authority':'R392 / Registry455 / Products52 / Quality39','r393_shadow_frontier':'15578 fresh pairs / 649 clusters / no product promotion'},indent=2))
 return 1 if e else 0
if __name__=='__main__':raise SystemExit(main())
