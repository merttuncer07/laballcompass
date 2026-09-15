from __future__ import annotations

import csv
import hashlib
import zipfile
from pathlib import Path


ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parent
NAME='LABALLCOMPASS_FOUNDRY_COMPLETED_P145_2026-08-25'
ZIP=WORKSPACE/f'{NAME}.zip'
SHA=WORKSPACE/f'{NAME}.zip.sha256'
MANIFEST=ROOT/'MANIFEST_SHA256.tsv'


def included(path:Path)->bool:
    relative=path.relative_to(ROOT)
    return not any(part in {'__pycache__','.pytest_cache'} for part in relative.parts) and path.suffix!='.pyc' and path!=MANIFEST


def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()


files=sorted(path for path in ROOT.rglob('*') if path.is_file() and included(path))
with MANIFEST.open('w',encoding='utf-8',newline='') as f:
    writer=csv.writer(f,delimiter='\t'); writer.writerow(['sha256','size_bytes','path'])
    for path in files:
        data=path.read_bytes(); writer.writerow([digest(data),len(data),path.relative_to(ROOT).as_posix()])

files.append(MANIFEST); files.sort()
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
    for path in files:
        zf.write(path,f'{NAME}/{path.relative_to(ROOT).as_posix()}')

zip_hash=digest(ZIP.read_bytes()); SHA.write_text(f'{zip_hash}  {ZIP.name}\n',encoding='ascii')

# Independent readback of every entry plus the embedded file manifest.
with zipfile.ZipFile(ZIP) as zf:
    bad_crc=zf.testzip()
    prefix=f'{NAME}/'
    manifest_rows=list(csv.DictReader(zf.read(prefix+'MANIFEST_SHA256.tsv').decode('utf-8').splitlines(),delimiter='\t'))
    mismatches=[]
    for row in manifest_rows:
        data=zf.read(prefix+row['path'])
        if len(data)!=int(row['size_bytes']) or digest(data)!=row['sha256']:mismatches.append(row['path'])
    entry_count=len([i for i in zf.infolist() if not i.is_dir()])

if bad_crc or mismatches:raise SystemExit(f'release verification failed: crc={bad_crc}, hashes={mismatches[:3]}')
print(f'zip={ZIP}')
print(f'sha256={zip_hash}')
print(f'entries={entry_count}')
print(f'manifest_rows={len(manifest_rows)}')
print('verification=PASS')
