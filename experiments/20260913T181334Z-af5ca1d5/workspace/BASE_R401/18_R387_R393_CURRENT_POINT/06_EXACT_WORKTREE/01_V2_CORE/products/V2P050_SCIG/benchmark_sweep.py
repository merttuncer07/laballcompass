from __future__ import annotations
import importlib.util, json, pathlib, sys
import numpy as np
from scig import support_covariance_independence_guard
ROOT=pathlib.Path(__file__).resolve().parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
SACPS=load('sacps_v2p050_sweep',ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R037_SUPPORT_COVARIANCE_SACPS/sacps.py')
CSID=load('csid_v2p050_sweep',ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS/IM445_IM085_CSID/csid.py')
FAIL=[CSID.FailureMode('reporting_failure',.5,100.)]
SAFE=[CSID.Safeguard('A',5.,'feed_A',{'reporting_failure':.6}),CSID.Safeguard('B',5.,'feed_B',{'reporting_failure':.6}),CSID.Safeguard('C',7.,'governance',{'reporting_failure':.5})]
rows=[]
for n in (80,160,400):
  for rho in (0.0,.25,.5,.6,.7,.9):
    counts={'SUPPORT_COVARIANCE_COLLAPSED_TO_DECLARED_FAMILIES':0,'ABSTAIN_DEPENDENCE_THRESHOLD_AMBIGUOUS':0,'SUPPORT_COVARIANCE_CHANGED_CSID_INDEPENDENCE_PARTITION':0}
    gains=[]; selected=[]; corrs=[]
    for seed in range(12):
      rng=np.random.default_rng(seed); z=rng.normal(size=n); b=rho*z+np.sqrt(max(0.,1-rho*rho))*rng.normal(size=n); e=np.column_stack((z,b,rng.normal(size=n)))
      s=np.eye(3,dtype=bool); s[0,1]=s[1,0]=True
      r=support_covariance_independence_guard(CSID,SACPS.estimate_support_aware_covariance,FAIL,SAFE,e,s,budget=12.,correlation_threshold=.6,ambiguity_band=.05,shrinkage_grid=[0.])
      counts[r['status']]+=1
      if r['status']!='ABSTAIN_DEPENDENCE_THRESHOLD_AMBIGUOUS':
        gains.append(r['gain_vs_declared_family_removal_control_under_adjusted_reality'])
        selected.append(r['candidate_dependence_adjusted_partition']['selected']['safeguards'])
        edge=r['cross_family_covariance_edges'][0] if r['cross_family_covariance_edges'] else None
        if edge: corrs.append(edge['absolute_correlation'])
    rows.append({'sample_size':n,'true_rho':rho,'status_counts':counts,'mean_gain_nonabstain':float(np.mean(gains)) if gains else None,'min_gain_nonabstain':float(np.min(gains)) if gains else None,'max_gain_nonabstain':float(np.max(gains)) if gains else None,'selected_portfolios_nonabstain':selected,'mean_observed_abs_corr_nonabstain':float(np.mean(corrs)) if corrs else None})
out={'model_version':'R389_SCIG_SENSITIVITY_SWEEP_V1','threshold':.6,'ambiguity_band':.05,'seeds_per_cell':12,'mechanism_removing_comparator':'same CSID shell with covariance-based cross-family partition repair removed','interpretation':'Clear low-correlation supported edges should collapse to declared CSID families; clear high-correlation supported edges should merge and can change portfolio choice; finite-sample cases near the threshold should abstain rather than force a merge. This is deterministic synthetic sensitivity evidence only.','rows':rows}
path=pathlib.Path(__file__).with_name('BENCHMARK_SWEEP_RESULT.json'); path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n'); print(json.dumps({'cells':len(rows),'low_rho_collapsed':all(r['status_counts']['SUPPORT_COVARIANCE_CHANGED_CSID_INDEPENDENCE_PARTITION']==0 for r in rows if r['true_rho']<=.25),'rho_0_9_all_merge':all(r['status_counts']['SUPPORT_COVARIANCE_CHANGED_CSID_INDEPENDENCE_PARTITION']==12 for r in rows if r['true_rho']==.9),'threshold_region_has_abstention':any(r['status_counts']['ABSTAIN_DEPENDENCE_THRESHOLD_AMBIGUOUS']>0 for r in rows if r['true_rho'] in (.5,.6,.7))},indent=2))
