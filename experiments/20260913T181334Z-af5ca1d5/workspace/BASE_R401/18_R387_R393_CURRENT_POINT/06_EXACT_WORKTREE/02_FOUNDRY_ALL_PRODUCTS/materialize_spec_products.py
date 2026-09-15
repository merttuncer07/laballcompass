from __future__ import annotations

import json
import re
from pathlib import Path


ROOT=Path(__file__).resolve().parent
CATALOG=ROOT.parent/'lcb_core_revision'/'generated'/'FOUNDRY_PRODUCT_CATALOG.jsonl'
PRODUCTS=ROOT/'products'
TARGETS=set(range(57,69))|set(range(75,106))|set(range(114,134))


def mode_for(text: str) -> str:
    value=text.lower()
    if any(word in value for word in ('tipping','threshold','surface','cliff')): return 'tipping'
    if any(word in value for word in ('audit','guard','certificate','holdout','validation')): return 'audit'
    if any(word in value for word in ('allocation','controller','acquisition','triage','portfolio','budget')): return 'allocation'
    return 'selection'


rows=[]
for line in CATALOG.read_text(encoding='utf-8').splitlines():
    row=json.loads(line)
    number=int(row['product_id'][1:])
    if number in TARGETS: rows.append(row)

for row in rows:
    product_id=row['product_id']; short=row['short_name']; directory=f'{product_id}_{short}'
    target=PRODUCTS/directory
    if target.exists():
        continue
    target.mkdir(parents=True)
    module=short.lower()
    spec={
        'product_id':product_id,
        'short_name':short,
        'title':row['title'],
        'parents_raw':row['parents_raw'],
        'historical_promotion_state':row['promotion_state'],
        'claim_boundary_raw':row['weakness_raw'],
        'execution_mode':mode_for(' '.join((row['title'],row['parents_raw'],row['weakness_raw']))),
    }
    source=(
        'from products.spec_runtime import evaluate_spec_product\n\n'
        f'PRODUCT_SPEC = {spec!r}\n\n'
        'def evaluate(records, *, baseline=None, budget=None):\n'
        '    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)\n'
    )
    test=(
        f'from .{module} import *\n\n'
        "def test_identity_preserved(): assert PRODUCT_SPEC['product_id'].startswith('P') and PRODUCT_SPEC['short_name']\n"
        "def test_reconstruction_tier_explicit():\n"
        " records=[{'name':'a','score':1,'value':1,'cost':1,'parameter':0,'decision':False,'selection_score':2,'protected_score':0},{'name':'b','score':2,'value':2,'cost':1,'parameter':1,'decision':True,'selection_score':1,'protected_score':3}]\n"
        " kwargs={'budget':1} if PRODUCT_SPEC['execution_mode']=='allocation' else ({'baseline':records[0]} if PRODUCT_SPEC['execution_mode']=='tipping' else {})\n"
        " assert evaluate(records,**kwargs)['reconstruction_tier']=='SPEC_EXECUTABLE_NOT_HISTORICAL_SOURCE'\n"
        "def test_empty_input_rejected():\n"
        " try: evaluate([])\n"
        " except ValueError: return\n"
        " assert False\n"
    )
    (target/'__init__.py').write_text(f'from .{module} import *\n',encoding='utf-8')
    (target/f'{module}.py').write_text(source,encoding='utf-8')
    (target/f'test_{module}.py').write_text(test,encoding='utf-8')
    (target/'RECONSTRUCTION_STATUS.md').write_text(
        f"# {product_id} {short} reconstruction status\n\n"
        "Historical result/provenance survived; historical source and tests did not. "
        "This package is a conservative spec-executable reconstruction, not a claim of byte-identical recovery.\n",
        encoding='utf-8',
    )

print(json.dumps({'materialized':len(rows),'targets':sorted(TARGETS)}))
