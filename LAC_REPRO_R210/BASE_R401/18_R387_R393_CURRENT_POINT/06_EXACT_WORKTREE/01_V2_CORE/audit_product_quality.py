from __future__ import annotations
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parent
P=ROOT/'products'
REQUIRED=('new_failure_mode','non_additive_interaction','nearest_existing_product','difference_from_nearest','mechanism_removing_comparator')

def test_count(path:Path)->int:
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_') for n in ast.walk(tree))

def audit(start=29,end=38):
    rows=[]
    for n in range(start,end+1):
        ds=list(P.glob(f'V2P{n:03d}_*'))
        if len(ds)!=1: rows.append({'product_id':f'V2P{n:03d}','status':'FAIL','reason':'directory cardinality'}); continue
        d=ds[0]; review=d/'NOVELTY_REVIEW.json'; bench=d/'BENCHMARK_RESULT.json'; comp=d/'COMPOSITION.json'; tests=list(d.glob('test_*.py'))
        errors=[]
        if not review.exists(): errors.append('missing novelty review')
        else:
            r=json.loads(review.read_text())
            if r.get('verdict')!='DISTINCT_PRODUCT': errors.append('not distinct-product verdict')
            for k in REQUIRED:
                if not str(r.get(k,'')).strip(): errors.append(f'missing {k}')
        if not bench.exists(): errors.append('missing benchmark result')
        else:
            b=json.loads(bench.read_text())
            if 'mechanism_removing_comparator' not in b: errors.append('benchmark missing mechanism-removing comparator')
            if not str(b.get('evidence_boundary','')).strip(): errors.append('benchmark missing evidence boundary')
        if not comp.exists(): errors.append('missing composition identity')
        if len(tests)!=1: errors.append('expected exactly one focused test module')
        elif test_count(tests[0])<8: errors.append('fewer than 8 focused contract tests')
        rows.append({'product_id':d.name.split('_',1)[0],'directory':d.name,'status':'PASS' if not errors else 'FAIL','errors':errors,'test_count':0 if not tests else test_count(tests[0])})
    return rows

if __name__=='__main__':
    rows=audit(); print(json.dumps({'rows':rows,'pass':sum(r['status']=='PASS' for r in rows),'fail':sum(r['status']=='FAIL' for r in rows)},indent=2)); raise SystemExit(1 if any(r['status']!='PASS' for r in rows) else 0)
