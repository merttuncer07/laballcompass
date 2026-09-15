"""Execute an existing experiment in a fresh copy, preserving its frozen source outputs."""
import json,shutil,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
from maintenance.runner import BASE,ROOT,atomic,environment,process_run,sha,now

def execute(folder,entry='run_experiment.py',timeout=180,root=ROOT,runs=BASE/'experiments'):
 root=Path(root).resolve();component=(root/folder).resolve()
 if not component.is_relative_to(root) or not component.is_dir():raise ValueError('Experiment folder must be inside the lab source root')
 script=(component/entry).resolve()
 if not script.is_relative_to(component) or not script.is_file() or script.suffix!='.py':raise ValueError('Entry must be a Python file inside the component')
 if timeout<=0:raise ValueError('Timeout must be positive')
 run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 out=Path(runs).resolve()/run_id;out.mkdir(parents=True)
 receipt={'run_id':run_id,'status':'PREPARING','started_at':now(),'folder':str(component.relative_to(root)),'entry':entry,'environment':environment(),'scope':'execution_only; no scientific promotion','workspace_boundary':'A file copy, not an operating-system security sandbox. Scripts with absolute paths or external side effects require separate review.'}
 path=out/'receipt.json';atomic(path,receipt)
 try:
  # Full relative tree preserves cross-component imports. Source is never edited.
  workspace=out/'workspace';shutil.copytree(root,workspace,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
  before={str(p.relative_to(workspace)):sha(p) for p in workspace.rglob('*') if p.is_file()}
  atomic(out/'input-hashes.json',before);receipt['input_snapshot_sha256']=sha(out/'input-hashes.json')
  receipt['status']='RUNNING';atomic(path,receipt)
  result=process_run([sys.executable,str(workspace/script.relative_to(root))],workspace/component.relative_to(root),out/'execution.log',timeout)
  receipt.update(result);receipt['status']='EXECUTED' if result['status']=='COMPLETED' and result['exit_code']==0 else result['status'] if result['status']!='COMPLETED' else 'FAIL'
  changes=[]
  for p in workspace.rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   rel=str(p.relative_to(workspace));digest=sha(p)
   if digest!=before.get(rel):changes.append({'path':rel,'sha256':digest,'change':'modified' if rel in before else 'created'})
  receipt['artifacts']=changes
  receipt['deleted_files']=[rel for rel in before if not (workspace/rel).exists()]
 except Exception as e:
  receipt.update(status='ERROR',reason=str(e));raise
 finally:
  receipt['finished_at']=now();atomic(path,receipt)
 return path
