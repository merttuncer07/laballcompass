from pathlib import Path
import os,sys,subprocess,json,time,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]/'LAC_REPRO_R210'
FOUNDRY=ROOT/'BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/02_FOUNDRY_ALL_PRODUCTS'
OUT=Path(__file__).resolve().parent/'baseline';OUT.mkdir(exist_ok=True)
def run(p):
 label=p.parent.name+'__'+p.stem
 start=time.monotonic();env=os.environ.copy();env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
 try:
  r=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',str(p)],cwd=FOUNDRY,env=env,capture_output=True,text=True,timeout=60)
  (OUT/(label+'.log')).write_text(r.stdout+r.stderr)
  row={'label':label,'source':str(p.relative_to(ROOT)),'exit':r.returncode,'seconds':round(time.monotonic()-start,2)}
 except subprocess.TimeoutExpired:row={'label':label,'exit':'TIMEOUT'}
 print(label,row['exit'],flush=True);return row
if __name__=='__main__':
 paths=sorted((FOUNDRY/'products').rglob('test_*.py'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,paths))
 (OUT/'foundry-summary.json').write_text(json.dumps(rows,indent=2));print('FAILED',sum(r['exit']!=0 for r in rows),'OF',len(rows),flush=True)
