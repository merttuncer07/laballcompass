"""Build a source-derived catalog; reported promotion is separate from observed tests."""
import ast,json
from pathlib import Path
from maintenance.runner import BASE,ROOT,CORE,sha,atomic

def build():
 latest={}
 for p in sorted((BASE/'runs').glob('*/receipt.json')):
  r=json.loads(p.read_text());grouped={}
  for t in r['targets']:
   source=Path(t['cwd'])
   if t.get('layer')=='foundry':source/=Path(t['pattern']).parent
   grouped.setdefault(source.as_posix(),[]).append(t)
  for source,targets in grouped.items():
   statuses=[t['status'] for t in targets]
   status='PASS' if all(s=='PASS' for s in statuses) else 'FAIL' if any(s in ('FAIL','ERROR','TIMEOUT') for s in statuses) else 'INCOMPLETE'
   latest[source]={'status':status,'receipt':str(p.relative_to(BASE)),'scope':'All selected targets for this component in this run; see receipt for exact tests.'}
 rows=[]
 def record(p,layer,declared='Not asserted by maintenance layer',fidelity='Packaged source'):
  files=sorted(x for x in p.glob('*.py') if not x.name.startswith(('test_','demo_','run_','__')))
  imports=[];apis=[];interfaces=[];description=''
  for f in files:
   try:
    tree=ast.parse(f.read_text());description=description or ast.get_docstring(tree) or ''
    for assignment in tree.body:
     if isinstance(assignment,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRODUCT_SPEC' for t in assignment.targets):
      try: spec=ast.literal_eval(assignment.value)
      except (ValueError,TypeError): continue
      if isinstance(spec,dict) and str(spec.get('implementation_version','')).startswith('native_reimplementation_'):
       fidelity='New native implementation; original historical source remains unavailable'
    for n in ast.walk(tree):
     if isinstance(n,ast.ImportFrom):imports.append(n.module or '')
     elif isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
    apis.extend(n.name for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and not n.name.startswith('_'))
    for n in tree.body:
     if isinstance(n,ast.FunctionDef) and not n.name.startswith('_'):interfaces.append(n.name+'('+ast.unparse(n.args)+')')
     if isinstance(n,ast.ClassDef):
      for m in n.body:
       if isinstance(m,ast.FunctionDef) and (not m.name.startswith('_') or m.name=='__init__'):interfaces.append(n.name+'.'+m.name+'('+ast.unparse(m.args)+')')
   except (SyntaxError,UnicodeError):pass
  relative=p.relative_to(ROOT).as_posix()
  demos=sorted({f.name for pattern in ('demo*.py','run_experiment.py') for f in p.glob(pattern)})
  if any('shared_foundry' in s for s in imports):fidelity='Shared reference reconstruction; not the lost historical implementation'
  if any('spec_runtime' in s for s in imports):fidelity='Generic spec_runtime replacement; historical implementation equivalence unverified'
  rows.append({'id':p.name,'layer':layer,'description':description,'declared_status':declared,'source_fidelity':fidelity+'; change records: restoration/source-changes.json and restoration/20260914-product-repairs/changes.json and restoration/20260914-rel-content/changes.json','source_directory':relative,'python_sources':[{'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)} for f in files],'public_api':apis,'interfaces':interfaces,'demo_entries':demos,'direct_test_files':[f.name for f in sorted(p.glob('test_*.py'))],'latest_reproduction':latest.get(relative,{'status':'NOT_RUN','receipt':None}),'scientific_validity':'NOT_ESTABLISHED_BY_TEST_PASS'})
 for tier in ('CURRENT_PRODUCTS','RETRO_PRODUCTS'):
  for p in sorted((ROOT/CORE/'02_FOUNDRY_ALL_PRODUCTS/parent_products'/tier).iterdir()):
   if p.is_dir() and any(p.glob('*.py')):record(p,'parent',tier)
 for p in sorted((ROOT/CORE/'02_FOUNDRY_ALL_PRODUCTS/products').glob('P*')):
  if p.is_dir():record(p,'foundry')
 for p in sorted((ROOT/CORE/'01_V2_CORE/products').glob('V2P*')):
  if p.is_dir():record(p,'V2')
 for group in ('ACTIVE_RESEARCH','ACTIVE_PRODUCTS'):
  for p in sorted((ROOT/group).iterdir()):
   if p.is_dir():record(p,group)
 for d in ROOT.rglob('material_products'):
  for p in sorted(d.iterdir()):
   if p.is_dir():record(p,'R401_material')
 # Recovered work remains explicitly separate. Do not upgrade it from a historical receipt.
 for p in ROOT.rglob('02_PRODUCT_LEDGER_R394_R398.jsonl'):
  for line in p.read_text().splitlines():
   r=json.loads(line);rows.append({'id':r['product_id']+'_'+r['short_name'],'layer':'recovered_V2','description':r['mechanism'],'declared_status':r['status'],'source_fidelity':r['source_fidelity'],'source_directory':str(p.parent.relative_to(ROOT)),'ledger':str(p.relative_to(ROOT)),'latest_reproduction':latest.get(str((p.parent/'RECOVERED_REFERENCE_CODE').relative_to(ROOT)),{'status':'NOT_RUN','receipt':None}),'scientific_validity':'NOT_ESTABLISHED_BY_TEST_PASS','limitations':r['failure_or_collapse']})
 atomic(BASE/'catalog.json',{'schema_version':1,'components':rows,'boundary':'Source-derived inventory. Exact manifest verifies bytes; tests verify declared surfaces. Neither proves originality, validity beyond experiments or product readiness.'})
 return len(rows)
if __name__=='__main__':print(build(),'components')
