from pathlib import Path
import subprocess,sys,re,time,json,argparse
ROOT=Path(__file__).resolve().parents[1]; core=ROOT/'01_V2_CORE'
parts={
 'a':['test_core_v2.py','test_core_v2_foundry_integration.py','test_lab_search_engine.py','test_search_corpus_integration.py','test_relevance_learning.py','test_experiment_selector.py','test_experiment_telemetry.py','test_experiment_integration.py'],
 'b':['test_experiment_contract_bootstrap.py','test_r12_closure.py','test_r387_product_overlay_closure.py','test_r388_retro50_parent_integration_closure.py','test_r389_product_overlay_closure.py','test_r390_product_overlay_closure.py','test_r391_product_overlay_closure.py']}
ap=argparse.ArgumentParser(); ap.add_argument('part',choices=parts); a=ap.parse_args(); scripts=parts[a.part]
runs=[]; start=time.time()
for script in scripts:
 cp=subprocess.run([sys.executable,script],cwd=core,text=True,capture_output=True,timeout=90)
 text=cp.stdout+'\n'+cp.stderr; m=re.search(r'Ran (\d+) tests?',text)
 runs.append({'script':script,'exit_code':cp.returncode,'tests':int(m.group(1)) if m else None,'stdout':cp.stdout[-1500:],'stderr':cp.stderr[-2500:]})
out={'release':'R391','part':a.part,'run_count':len(runs),'tests_counted':sum(r['tests'] or 0 for r in runs),'failed':[r['script'] for r in runs if r['exit_code']!=0],'status':'PASS' if all(r['exit_code']==0 for r in runs) else 'FAIL','elapsed_seconds':round(time.time()-start,3),'runs':runs}
p=ROOT/f'08_R391_NATIVE_ROUTING/R391_SPLIT_CORE_REGRESSION_{a.part}.json'; p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('part','run_count','tests_counted','failed','status','elapsed_seconds')},indent=2))
raise SystemExit(0 if out['status']=='PASS' else 1)
