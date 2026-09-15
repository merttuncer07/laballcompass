from pathlib import Path
import subprocess,sys,re,json,time
ROOT=Path(__file__).resolve().parents[1]; core=ROOT/'01_V2_CORE'
scripts=['test_core_v2_foundry_integration.py','test_r12_closure.py','test_r387_product_overlay_closure.py','test_r388_retro50_parent_integration_closure.py','test_r389_product_overlay_closure.py','test_r390_product_overlay_closure.py','test_r391_product_overlay_closure.py']
runs=[]; start=time.time()
for script in scripts:
 cp=subprocess.run([sys.executable,script],cwd=core,text=True,capture_output=True,timeout=90); text=cp.stdout+'\n'+cp.stderr; m=re.search(r'Ran (\d+) tests?',text)
 runs.append({'script':script,'exit_code':cp.returncode,'tests':int(m.group(1)) if m else None,'stderr':cp.stderr[-2500:]})
out={'release':'R391','status':'PASS' if all(r['exit_code']==0 for r in runs) else 'FAIL','surfaces':len(runs),'tests_counted':sum(r['tests'] or 0 for r in runs),'failed':[r['script'] for r in runs if r['exit_code']!=0],'runs':runs,'note':'Historical release audits preserve their own counts while live-state assertions are future-release-safe.'}
(ROOT/'08_R391_NATIVE_ROUTING/R391_POSTPROMOTION_CLOSURE_RECEIPT.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({k:out[k] for k in ['release','status','surfaces','tests_counted','failed']},indent=2)); raise SystemExit(0 if out['status']=='PASS' else 1)
