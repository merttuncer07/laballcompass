"""Compare exact source representations on unchanged regulator workbook bytes."""
import hashlib,json,resource,sys,time,types
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from workbench.workbooks import analyze_workbook
mode=sys.argv[1];output=Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=True);
assert mode in ('compact','legacy')
if (output/(mode+'-sets.json')).exists():raise SystemExit('Use a new result path; existing observations are preserved')
folder=Path(__file__).parent;path=folder/'sources/soni-financial-model.xlsx'
legacy=root/'restoration/20260916-lineage-semantics/before/workbench/workbooks.py'
if mode=='legacy':
 source=legacy.read_text();assert 'membership_count > 500000' in source
 module=types.ModuleType('workbench._legacy_reference');module.__package__='workbench'
 exec(compile(source.replace('membership_count > 500000','membership_count > 10000000'),str(legacy),'exec'),module.__dict__)
 analyze_workbook=module.analyze_workbook
started=time.perf_counter();problem=analyze_workbook(path);elapsed=time.perf_counter()-started
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
document=problem.to_dict();document['metadata'].pop('function_range_adjustments',None)
# Source positions, declared formulas, roots and same-origin groups all remain included.
digest=hashlib.sha256(json.dumps(document,sort_keys=True).encode()).hexdigest()
result={'mode':mode,'seconds':elapsed,'process_peak_rss_bytes_before_serialization':peak,'full_problem_sha256_without_new_empty_field':digest,'sources':len(problem.sources),'formulas':len(problem.rules),'targets':len(problem.targets),'same_origin_groups':len(problem.metadata['same_origin_groups']),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'legacy_reference_budget_change':'500000 to 10000000 transitive memberships solely to allow exact reference comparison' if mode=='legacy' else None}
(output/(mode+'-sets.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
