from __future__ import annotations
import json, pathlib, numpy as np
from test_sacdlw import run
rows=[]
for rho in (0.0,-.25,-.5,-.75,-.9,-.95):
  gains=[]; changed=0; abstain=0
  for seed in range(12):
    r=run(risk_aversion=40.,seed=seed,support_limit=.12,spurious_correlation=rho)
    if r['status'].startswith('ABSTAIN_'):
      abstain+=1; continue
    gains.append(r['validation_reference_regret_gain_vs_raw_covariance'])
    changed += int(r['candidate_selected_model']!=r['control_selected_model'] or not r['candidate_actions_equal_control'])
  rows.append({'declared_training_nuisance_correlation':rho,'nonabstain':len(gains),'abstain':abstain,'changed_geometry_cases':changed,'positive_gain_cases':sum(g>0 for g in gains),'mean_reference_regret_gain':None if not gains else float(np.mean(gains)),'min_reference_regret_gain':None if not gains else float(np.min(gains)),'max_reference_regret_gain':None if not gains else float(np.max(gains))})
zero=[]
for seed in range(12):
  r=run(risk_aversion=0.,seed=seed,support_limit=.12,spurious_correlation=-.95)
  zero.append({'seed':seed,'gain':r['validation_reference_regret_gain_vs_raw_covariance'],'changed':r['candidate_selected_model']!=r['control_selected_model'] or not r['candidate_actions_equal_control']})
out={'model_version':'R390_V2P051_SACDLW_SENSITIVITY_V2','seeds_per_cell':12,'rows':rows,'zero_risk_collapse':zero,'interpretation':'Synthetic sensitivity only. Strong unsupported negative covariance in the small risk-estimation sample creates the declared working region; benefit is not universal across seeds. Zero risk aversion must collapse exactly.'}
path=pathlib.Path(__file__).with_name('BENCHMARK_SWEEP_RESULT.json'); path.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
