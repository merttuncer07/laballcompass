"""Resolve and operate lab components by stable IDs instead of historical paths."""
import argparse,json,sys
from pathlib import Path
from maintenance.runner import BASE,ROOT,discover,run
from maintenance.catalog import collect
from maintenance.experiment import execute

def catalog():
 return collect()['components']
def resolve(query):
 rows=collect(component=query)['components'];exact=[r for r in rows if r['id']==query]
 matches=exact or [r for r in rows if r['id'].split('_')[0]==query]
 if len(matches)!=1:raise ValueError('Use one exact component ID. Matches: '+', '.join(r['id'] for r in matches))
 return matches[0]
def target_matches(row,target):
 path=Path(target.cwd)
 if target.layer=='foundry':path/=Path(target.pattern).parent
 if row['layer']=='recovered_V2':return target.layer=='recovered'
 return path.as_posix()==row['source_directory']
def main(args):
 p=argparse.ArgumentParser();p.add_argument('action',choices=['components','show','check','demo']);p.add_argument('id',nargs='?');p.add_argument('--query',default='');p.add_argument('--entry');p.add_argument('--timeout',type=float,default=180);p.add_argument('--limit',type=int,default=20);p.add_argument('--offset',type=int,default=0);p.add_argument('--quiet',action='store_true');a=p.parse_args(args)
 try:
  if a.action=='components':
   if a.limit<1 or a.offset<0:raise ValueError('Use a positive limit and nonnegative offset')
   matches=[r for r in catalog() if a.query.lower() in json.dumps(r).lower()]
   for r in matches[a.offset:a.offset+a.limit]:
    print(f"{r['id']:38} {r['layer']:16} observed={r['latest_reproduction']['status']}")
   print(f'{len(matches)} matches; offset={a.offset}, limit={a.limit}. Observed results are historical, not verified against current source.')
   return 0
  if not a.id:p.error('A component ID is required')
  row=resolve(a.id)
  if a.action=='show':print(json.dumps(row,indent=2,ensure_ascii=False));return 0
  if a.action=='check':
   targets=[t for t in discover('all') if target_matches(row,t)]
   if not targets:raise ValueError('No existing test target found for this component')
   path=run(targets,profile='component:'+row['id'],timeout=a.timeout,quiet=a.quiet);print(path);return int(json.loads(path.read_text())['status']!='PASS')
  entries=row.get('demo_entries',[])
  if not entries:raise ValueError('No shipped demo entry; use show for the public API or check for existing examples in tests')
  entry=a.entry or (entries[0] if len(entries)==1 else None)
  if entry not in entries:raise ValueError('Choose --entry from: '+', '.join(entries))
  path=execute(row['source_directory'],entry,timeout=a.timeout);print(path);return int(json.loads(path.read_text())['status']!='EXECUTED')
 except (ValueError,OSError) as e:p.error(str(e))
