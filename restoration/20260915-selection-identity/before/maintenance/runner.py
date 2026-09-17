"""Durable local runner for the original LabAllCompass test surfaces."""
from __future__ import annotations
import argparse,fnmatch,hashlib,importlib.metadata,json,os,platform,signal,subprocess,sys,time,uuid
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'LAC_REPRO_R210'
CORE=Path('BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE')
MATERIAL=Path('BASE_R401/22_R399_R401_CURRENT_DELTA/LABALLCOMPASS_R401_MATERIAL_PRODUCT_REVIEW_2026-08-31/material_products')

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic(path,value):
 path=Path(path);tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
 tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');os.replace(tmp,path)
@dataclass
class Target:
 id:str
 cwd:str
 runner:str
 pattern:str='test_*.py'
 layer:str='active'

def discover(profile='full',root=ROOT):
 targets=[]
 if profile in ('active','full','all'):
  for p in sorted((root/'ACTIVE_RESEARCH').glob('R*')):
   if p.is_dir():targets.append(Target(p.name,p.relative_to(root).as_posix(),'pytest'))
  for p in sorted((root/'ACTIVE_PRODUCTS').iterdir()):
   if p.is_dir():targets.append(Target(p.name,p.relative_to(root).as_posix(),'pytest'))
  for p in sorted((root/MATERIAL).iterdir()):
   if p.is_dir():targets.append(Target('R401_'+p.name,p.relative_to(root).as_posix(),'unittest',layer='material'))
 if profile in ('embedded','full','all'):
  for p in sorted((root/CORE/'01_V2_CORE/products').glob('V2P*')):
   if p.is_dir() and any(p.glob('test_*.py')):targets.append(Target('R392_'+p.name,p.relative_to(root).as_posix(),'unittest',layer='V2'))
  for p in sorted((root/CORE/'01_V2_CORE').glob('test_*.py')):
   targets.append(Target('R392_CORE_'+p.stem,p.parent.relative_to(root).as_posix(),'unittest',p.name,'core'))
 if profile in ('parents','all'):
  for tier in ('CURRENT_PRODUCTS','RETRO_PRODUCTS'):
   for p in sorted((root/CORE/'02_FOUNDRY_ALL_PRODUCTS/parent_products'/tier).iterdir()):
    if p.is_dir() and any(p.glob('test_*.py')):targets.append(Target(p.name,p.relative_to(root).as_posix(),'unittest',layer='parent'))
 if profile in ('foundry','all'):
  foundry=root/CORE/'02_FOUNDRY_ALL_PRODUCTS'
  for p in sorted((foundry/'products').rglob('test_*.py')):
   targets.append(Target('FOUNDRY_'+p.parent.name+'__'+p.stem,foundry.relative_to(root).as_posix(),'pytest',p.relative_to(foundry).as_posix(),'foundry'))
 if profile in ('recovered','all'):
  for p in sorted(root.glob('BASE_R401/19*/RECOVERED_REFERENCE_CODE/test_*.py')):
   targets.append(Target('RECOVERED_'+p.stem,p.parent.relative_to(root).as_posix(),'pytest',p.name,'recovered'))
 if profile in ('repairs','all'):
  targets.append(Target('RESTORATION_REGRESSIONS','..','pytest','tests/restoration','restoration'))
 return targets

def environment():
 packages={}
 for p in ('numpy','scipy','pytest','iniconfig','packaging','pluggy','Pygments'):
  try:packages[p]=importlib.metadata.version(p)
  except importlib.metadata.PackageNotFoundError:packages[p]=None
 return {'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':packages}

def doctor():
 e=environment();missing=[p for p in ('numpy','scipy','pytest') if not e['packages'][p]]
 return {'status':'FAIL' if missing else 'PASS','missing':missing,'environment':e}

def terminate(process):
 if process.poll() is not None:return
 try:
  if os.name=='posix':os.killpg(process.pid,signal.SIGTERM)
  else:process.terminate()
  process.wait(timeout=3)
 except (ProcessLookupError,subprocess.TimeoutExpired):
  try:
   if os.name=='posix':os.killpg(process.pid,signal.SIGKILL)
   else:process.kill()
   process.wait(timeout=3)
  except ProcessLookupError:pass

def process_run(command,cwd,log,timeout):
 started=time.monotonic();p=None
 with open(log,'wb') as stream:
  try:
   env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONUNBUFFERED='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
   p=subprocess.Popen(command,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,env=env,start_new_session=os.name=='posix')
   try:code=p.wait(timeout=timeout);status='COMPLETED'
   except subprocess.TimeoutExpired:terminate(p);code=p.returncode;status='TIMEOUT'
  except KeyboardInterrupt:
   if p:terminate(p)
   return {'status':'INTERRUPTED','exit_code':p.returncode if p else None,'seconds':round(time.monotonic()-started,3)}
  except OSError as e:
   stream.write(str(e).encode());code=None;status='ERROR'
 return {'status':status,'exit_code':code,'seconds':round(time.monotonic()-started,3)}

def counts(path,kind):
 if kind=='unittest':
  d=json.loads(path.read_text());d['passed']=d['tests']-sum(d[k] for k in ('failures','errors','skipped','expected_failures','unexpected_successes'));return d
 tree=ElementTree.parse(path);cases=list(tree.iter('testcase'))
 result={'tests':len(cases),'failures':0,'errors':0,'skipped':0,'expected_failures':0,'unexpected_successes':0}
 for c in cases:
  for key,tag in [('failures','failure'),('errors','error'),('skipped','skipped')]:result[key]+=int(c.find(tag) is not None)
 result['passed']=result['tests']-sum(result[k] for k in ('failures','errors','skipped'))
 return result

def run(targets,root=ROOT,runs=BASE/'runs',timeout=180,verify=False,profile='custom'):
 if not targets:raise ValueError('No targets selected; refusing to produce a passing run.')
 if timeout<=0:raise ValueError('Timeout must be positive')
 root=Path(root).resolve();runs=Path(runs).resolve();runs.mkdir(parents=True,exist_ok=True)
 run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 directory=runs/run_id;directory.mkdir()
 receipt={'schema_version':1,'run_id':run_id,'status':'RUNNING','started_at':now(),'profile':profile,'source_root':str(root),'environment':environment(),'timeout_seconds':timeout,'targets':[dict(asdict(t),status='PENDING') for t in targets],'results_scope':'software_reproduction_only','input_manifest_sha256':sha(root/'04_FILE_MANIFEST_SHA256.tsv') if (root/'04_FILE_MANIFEST_SHA256.tsv').exists() else None}
 # Hash every Python file: imports may cross directories, so target-local hashes are insufficient.
 hashes={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*.py')) if '__pycache__' not in p.parts}
 for directory_name in ('maintenance','tests'):
  hashes.update({str(Path('..')/p.relative_to(BASE)):sha(p) for p in sorted((BASE/directory_name).rglob('*.py')) if '__pycache__' not in p.parts})
 atomic(directory/'source-hashes.json',hashes);receipt['source_snapshot_sha256']=sha(directory/'source-hashes.json')
 receipt['runner_sha256']=sha(__file__);receipt['worker_sha256']=sha(BASE/'maintenance/unittest_worker.py')
 receipt['integrity']={'status':'NOT_REQUESTED','scope':'Working source is hashed above; the historical package manifest is not a gate for development.'}
 path=directory/'receipt.json';atomic(path,receipt)
 def save():receipt['updated_at']=now();atomic(path,receipt)
 if verify:
  check=process_run([sys.executable,str(root/'verify_package.py')],root,directory/'integrity.log',timeout)
  receipt['integrity']=check;save()
  if check['status']!='COMPLETED' or check['exit_code']!=0:
   receipt.update(status='FAIL',finished_at=now(),reason='Source integrity verification failed');save();return path
 try:
  for index,(t,row) in enumerate(zip(targets,receipt['targets'])):
   row.update(status='RUNNING',started_at=now());save()
   result_file=directory/(f'{index:03}.xml' if t.runner=='pytest' else f'{index:03}.json')
   command=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',f'--junitxml={result_file}'] if t.runner=='pytest' else [sys.executable,str(BASE/'maintenance/unittest_worker.py'),str(result_file),t.pattern]
   if t.runner=='pytest' and t.pattern!='test_*.py':command.append(t.pattern)
   row['command']=command;row['log']=f'{index:03}.log';row['result_file']=result_file.name;save()
   observed=process_run(command,root/t.cwd,directory/row['log'],timeout)
   row.update(observed)
   if observed['status']=='COMPLETED':
    try:
     row['counts']=counts(result_file,t.runner)
     c=row['counts']
     row['status']='PASS' if observed['exit_code']==0 and c['passed']>0 and not any(c[k] for k in ('failures','errors','unexpected_successes')) else 'FAIL'
     if c['passed']==0:row['reason']='No tests passed; zero/skipped-only execution is not success.'
    except (OSError,ValueError,ElementTree.ParseError,KeyError) as e:row.update(status='ERROR',reason='Missing or invalid test report: '+str(e))
   row['finished_at']=now();save()
   print(f"{t.id}: {row['status']}",flush=True)
   if row['status']=='INTERRUPTED':break
 except KeyboardInterrupt:
  receipt['reason']='Runner interrupted between targets'
 finally:
  statuses=[r['status'] for r in receipt['targets']]
  receipt['status']='PASS' if all(s=='PASS' for s in statuses) else 'INCOMPLETE' if any(s in ('PENDING','RUNNING','INTERRUPTED') for s in statuses) else 'FAIL'
  receipt['finished_at']=now();receipt['counts']={k:sum(r.get('counts',{}).get(k,0) for r in receipt['targets']) for k in ('tests','passed','failures','errors','skipped','expected_failures','unexpected_successes')};save()
 return path

def main():
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['doctor','list','run']);parser.add_argument('--profile',choices=['active','embedded','full','parents','foundry','recovered','all','repairs'],default='active');parser.add_argument('--target',default='*');parser.add_argument('--timeout',type=float,default=180);parser.add_argument('--verify-package',action='store_true',help='Require the sealed package manifest to match before running tests; omit while editing source.');args=parser.parse_args()
 if args.action=='doctor':d=doctor();print(json.dumps(d,indent=2));return int(d['status']!='PASS')
 targets=[t for t in discover(args.profile) if fnmatch.fnmatchcase(t.id,args.target)]
 if args.action=='list':print(json.dumps([asdict(t) for t in targets],indent=2));return 0
 check=doctor()
 if check['status']!='PASS':print(json.dumps(check,indent=2));return 2
 try:path=run(targets,timeout=args.timeout,profile=args.profile,verify=args.verify_package)
 except ValueError as e:parser.error(str(e))
 print(path);return int(json.loads(path.read_text())['status']!='PASS')
if __name__=='__main__':sys.exit(main())
