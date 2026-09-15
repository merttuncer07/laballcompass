"""Seal restored bytes without erasing the original package manifest or change history."""
import csv,hashlib,io,json,zipfile,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'LAC_REPRO_R210';OUT=Path(__file__).parent
ZIP=Path('/Users/mertalituncer/Downloads/LABALLCOMPASS_ONLY_2026-09-13/LABALLCOMPASSREPRO.zip')
with zipfile.ZipFile(ZIP) as z:
 original=z.read('LAC_REPRO_R210/04_FILE_MANIFEST_SHA256.tsv');(OUT/'ORIGINAL_MANIFEST.tsv').write_bytes(original)
 rows=list(csv.DictReader(io.StringIO(original.decode()),delimiter='\t'));changes=[];patch=[]
 for row in rows:
  p=ROOT/row['path'];data=p.read_bytes();digest=hashlib.sha256(data).hexdigest()
  if digest!=row['sha256']:
   changes.append({'path':row['path'],'before_sha256':row['sha256'],'after_sha256':digest})
   if p.suffix in ('.py','.md','.json'):
    before=z.read('LAC_REPRO_R210/'+row['path']).decode(errors='replace').splitlines(keepends=True)
    patch.extend(difflib.unified_diff(before,data.decode(errors='replace').splitlines(keepends=True),fromfile='original/'+row['path'],tofile='restored/'+row['path']))
   row['sha256']=digest;row['bytes']=str(len(data))
 existing={r['path'] for r in rows}
 for p in ROOT.rglob('*'):
  rel=str(p.relative_to(ROOT))
  if p.is_file() and rel not in existing and rel!='04_FILE_MANIFEST_SHA256.tsv' and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts:
   rows.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'component':'restoration_addition'})
 with (ROOT/'04_FILE_MANIFEST_SHA256.tsv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['path','sha256','bytes','component'],delimiter='\t');w.writeheader();w.writerows(rows)
 (OUT/'source-changes.json').write_text(json.dumps(changes,indent=2));(OUT/'source.patch').write_text(''.join(patch))
 print(len(changes),'modified original files;',len(rows),'restored manifest entries')
