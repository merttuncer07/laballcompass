from __future__ import annotations

import ast
import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT=Path(__file__).resolve().parent
PRODUCTS=ROOT/'products'

ORIGINAL=set(range(1,8))|set(range(134,146))
SALVAGED_SOURCE={8,12,13}
MECHANISM_RECON=set(range(14,20))|set(range(25,51))
SPEC_RECON=set(range(57,69))|set(range(75,106))|set(range(114,134))
REPLACEMENTS=set(range(9,12))|set(range(20,25))|set(range(51,57))|set(range(69,75))|set(range(106,114))


def tier(number:int)->str:
    if number in ORIGINAL:return 'ORIGINAL_EXECUTABLE_MATERIAL'
    if number in SALVAGED_SOURCE:return 'SALVAGED_SOURCE_WITH_REBUILT_TESTS'
    if number in MECHANISM_RECON:return 'MECHANISM_RECONSTRUCTED_FROM_RESULTS'
    if number in SPEC_RECON:return 'SPEC_EXECUTABLE_FROM_RESULTS'
    if number in REPLACEMENTS:return 'NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID'
    raise ValueError(number)


def spec_from_module(directory:Path)->dict:
    for path in directory.glob('*.py'):
        if path.name.startswith(('test_','__init__')):continue
        try: tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        except SyntaxError:continue
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRODUCT_SPEC' for t in node.targets):
                return ast.literal_eval(node.value)
    return {}


def first_heading(directory:Path)->str:
    for name in ('HISTORICAL_PRODUCT_RESULT.md','PRODUCT_RESULT.md','README.md'):
        path=directory/name
        if path.exists():
            for line in path.read_text(encoding='utf-8-sig').splitlines():
                if line.startswith('# '):return line[2:].strip()
    return directory.name


def profile(title:str,mode:str)->tuple[list[str],list[str],list[str]]:
    text=title.lower(); strengths=[]; weaknesses=[]; tags=[]
    mapping={
      'audit':('protected-selection comparison','requires a representative protected shell'),
      'holdout':('untouched holdout diagnosis','holdout may not represent deployment'),
      'tipping':('nearest boundary localization','grid and calibration remain operator-declared'),
      'certificate':('explicit certificate scope','certificate must not transfer outside its shell'),
      'integral':('continuous-versus-discrete distinction','certificate failure is not universal impossibility'),
      'support':('support/overlap visibility','support diagnostics do not create missing observations'),
      'information':('decision-valued information routing','requires a declared uncertainty and cost model'),
      'acquisition':('cost-aware measurement choice','channel model may be misspecified'),
      'allocation':('constraint-aware allocation','objective and resource prices require calibration'),
      'decision':('downstream decision alignment','declared loss may omit real consequences'),
      'resilience':('hidden-mode consequence awareness','current exposure does not cover every future path'),
      'transport':('transport bottleneck accounting','topology/yield assumptions require deployment data'),
      'conservation':('source/sink or conservation accounting','numerical conservation is not physical validation'),
      'causal':('target/shell separation','does not establish unmeasured causal assumptions'),
      'manufact':('fabrication feasibility separation','requires process-specific physical calibration'),
      'liquidity':('capacity-constrained funding logic','financial/legal eligibility remains external'),
      'burnout':('stateful survivor-selection awareness','synthetic hazard parameters are not market calibration'),
    }
    for word,(strength,weakness) in mapping.items():
        if word in text:
            tags.append(word); strengths.append(strength); weaknesses.append(weakness)
    if not strengths:
        generic={'audit':('protected comparison','protected shell choice'), 'tipping':('boundary search','declared grid'), 'allocation':('budgeted selection','declared value/cost'), 'selection':('feasibility-gated selection','declared score')}
        strength,weakness=generic.get(mode,generic['selection']); strengths=[strength]; weaknesses=[weakness]; tags=[mode]
    return sorted(set(tags)),sorted(set(strengths)),sorted(set(weaknesses))


def main()->None:
    regression=json.loads((ROOT/'regression_summary.json').read_text(encoding='utf-8'))
    rows=[]
    for directory in sorted(PRODUCTS.glob('P[0-9][0-9][0-9]_*')):
        number=int(directory.name[1:4]); spec=spec_from_module(directory); title=spec.get('title') or first_heading(directory)
        mode=spec.get('execution_mode','selection')
        tags,strengths,weaknesses=profile(title,mode)
        rows.append({'product_id':f'P{number:03d}','short_name':directory.name.split('_',1)[1],'title':title,'tier':tier(number),'parents':spec.get('parents_raw','see PARENT_PROVENANCE.md / historical result'),'execution_mode':mode,'source_files':len([p for p in directory.rglob('*.py') if not p.name.startswith('test_')]),'test_files':len(list(directory.rglob('test_*.py'))),'tags':tags,'strengths':strengths,'weaknesses':weaknesses})
    assert len(rows)==145 and [r['product_id'] for r in rows]==[f'P{i:03d}' for i in range(1,146)]
    out=ROOT/'audit'; out.mkdir(exist_ok=True)
    (out/'PRODUCT_EVIDENCE_INVENTORY.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    with (out/'PRODUCT_EVIDENCE_INVENTORY.tsv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,delimiter='\t'); writer.writerow(['product_id','short_name','title','tier','parents','execution_mode','source_files','test_files'])
        for r in rows:writer.writerow([r[k] for k in ('product_id','short_name','title','tier','parents','execution_mode','source_files','test_files')])
    edges=[]
    for a in rows:
        for b in rows:
            if a is b:continue
            overlap=set(a['tags'])&set(b['tags'])
            if overlap and a['tier']!='NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID':
                edges.append((a['product_id'],b['product_id'],','.join(sorted(overlap)),a['strengths'][0],b['weaknesses'][0]))
    with (out/'COMPLEMENT_GRAPH.tsv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,delimiter='\t'); writer.writerow(['supplier','consumer','shared_tags','supplier_strength','consumer_gap']); writer.writerows(edges)
    counts=Counter(r['tier'] for r in rows)
    core=f'''# Foundry Core V2 — working epistemology and product-composition contract

## Objective

Build things that work and learn how to repair or redirect them. Academic acceptance and prior-art collision are information, not vetoes. Mathematics, executable behavior, physical constraints, and observed consequences remain hard constraints.

## Benchmark rule

A failed benchmark does **not** kill a product. It identifies a boundary among implementation defect, wrong use-case, missing adapter, calibration error, data-support failure, or genuine mechanism failure. Products remain available for another shell unless the mechanism itself is contradicted.

## Composition rule

Every product exposes strengths, weaknesses, input/output contracts, shell assumptions, and evidence tier. A composition is proposed when one product's strength addresses another's explicit weakness. Standalone productability is evaluated independently from integration value.

## Evidence tiers

{json.dumps(dict(counts),indent=2)}

These tiers must never be collapsed. “Spec-executable” means callable and tested contract reconstruction; it does not mean the missing historical algorithm was recovered. Gap replacements are new work.

## Current executable state

- Product IDs: P001–P145, contiguous and unique.
- Parent tests: {regression['parent_test_files']} files.
- Product tests: {regression['product_test_files']} files.
- Total: {regression['test_files_passed']} files / {regression['tests_counted']} tests / {regression['test_files_failed']} failures.
- Original agent rescue claims are retained as historical evidence only; the figures above are the fresh local regression.
'''
    (out/'FOUNDRY_CORE_V2.md').write_text(core,encoding='utf-8')
    summary={'products':len(rows),'tier_counts':dict(counts),'complement_edges':len(edges),'fresh_regression':{k:regression[k] for k in ('parent_test_files','product_test_files','test_files_passed','test_files_failed','tests_counted')}}
    (out/'FINAL_AUDIT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    (ROOT/'README_FINAL.md').write_text('# LABALLCOMPASS Foundry completion\n\nStart with `audit/FOUNDRY_CORE_V2.md`, `audit/FINAL_AUDIT_SUMMARY.json`, and `audit/PRODUCT_EVIDENCE_INVENTORY.tsv`. Run `python run_regression.py` for the fresh executable check.\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
