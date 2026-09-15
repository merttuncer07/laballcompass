"""Run shipped parent demos in one disposable full-tree copy; no frozen outputs overwritten."""
import concurrent.futures,json,os,shutil,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];ROOT=BASE/'LAC_REPRO_R210';OUT=BASE/'restoration/demo-run';OUT.mkdir(exist_ok=True)
WORK=BASE/'_workspaces/demos'
if not WORK.exists():shutil.copytree(ROOT,WORK,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
D=WORK/'BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/02_FOUNDRY_ALL_PRODUCTS/parent_products'
def component(p):
 rows=[]
 for script in sorted(p.glob('demo*.py')):
  start=time.monotonic();env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
  try:
   r=subprocess.run([sys.executable,str(script)],cwd=p,capture_output=True,text=True,env=env,timeout=45)
   log=p.name+'__'+script.name+'.log';(OUT/log).write_text(r.stdout+r.stderr)
   row={'component':p.name,'script':str(script.relative_to(WORK)),'status':'EXECUTED' if r.returncode==0 else 'FAIL','exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'log':log}
  except subprocess.TimeoutExpired:row={'component':p.name,'script':script.name,'status':'TIMEOUT'}
  print(row['component'],script.name,row['status'],flush=True);rows.append(row)
 return rows
if __name__=='__main__':
 dirs=sorted(p for tier in D.iterdir() if tier.is_dir() for p in tier.iterdir() if p.is_dir())
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=[r for group in pool.map(component,dirs) for r in group]
 (OUT/'receipt.json').write_text(json.dumps({'results':rows,'scope':'Shipped parent demo execution; not independent scientific validation'},indent=2));print('FAILURES',sum(r['status']!='EXECUTED' for r in rows),'OF',len(rows))
