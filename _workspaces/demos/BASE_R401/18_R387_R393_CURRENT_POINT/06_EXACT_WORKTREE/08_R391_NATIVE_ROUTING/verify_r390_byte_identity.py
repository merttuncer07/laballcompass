from pathlib import Path
import zipfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
ZIP=Path('/mnt/data/LABALLCOMPASS_FULL_CURRENT_POINT_ARCHIVE_R390_2026-08-30.zip')
PREFIX='LAB_R390_WORK/'
auth=json.loads((ROOT/'01_V2_CORE/CURRENT_PRODUCT_AUTHORITY.json').read_text())
if auth['authority_release']!='R390': raise RuntimeError('byte inheritance proof must be built before R391 promotion')
ids=set(auth['canonical_executable_suite_ids'])
def current_files(base):
 return {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
with zipfile.ZipFile(ZIP) as z:
 names=[n for n in z.namelist() if not n.endswith('/') and '/__pycache__/' not in n and not n.endswith('.pyc')]
 zprod={}; cprod={}
 for n in names:
  rel=n[len(PREFIX):] if n.startswith(PREFIX) else None
  if not rel or not rel.startswith('01_V2_CORE/products/V2P'): continue
  pid=Path(rel).parts[2].split('_',1)[0]
  if pid in ids: zprod[rel]=hashlib.sha256(z.read(n)).hexdigest()
 for p in (ROOT/'01_V2_CORE/products').rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
   pid=p.parent.name.split('_',1)[0]
   if pid in ids: cprod[str(p.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 zfound={}
 for n in names:
  rel=n[len(PREFIX):] if n.startswith(PREFIX) else None
  if rel and rel.startswith('02_FOUNDRY_ALL_PRODUCTS/'): zfound[rel]=hashlib.sha256(z.read(n)).hexdigest()
 cfound=current_files(ROOT/'02_FOUNDRY_ALL_PRODUCTS')
def compare(a,b):
 return {'byte_identical':a==b,'files_archive':len(a),'files_current':len(b),'missing_current':sorted(set(a)-set(b))[:20],'extra_current':sorted(set(b)-set(a))[:20],'changed':sorted(k for k in set(a)&set(b) if a[k]!=b[k])[:20]}
prod=compare(zprod,cprod); found=compare(zfound,cfound)
(ROOT/'08_R391_NATIVE_ROUTING/R391_R390_CANONICAL_PRODUCT_BYTE_IDENTITY.json').write_text(json.dumps(prod,indent=2)+'\n')
(ROOT/'08_R391_NATIVE_ROUTING/R391_R390_FOUNDRY_BYTE_IDENTITY.json').write_text(json.dumps(found,indent=2)+'\n')
print(json.dumps({'products':prod,'foundry':found},indent=2))
if not prod['byte_identical'] or not found['byte_identical']: raise SystemExit(1)
