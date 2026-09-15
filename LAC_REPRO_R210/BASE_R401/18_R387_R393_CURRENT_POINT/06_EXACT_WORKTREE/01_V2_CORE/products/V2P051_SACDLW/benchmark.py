from __future__ import annotations
import json, pathlib
from test_sacdlw import working, run
out={
  'model_version':'R390_V2P051_SACDLW_BENCHMARK_V1',
  'mechanism_removing_comparator':'same DLEW prediction candidates, outcomes, finite action set, initial action and transaction cost; only SACPS support-aware covariance is replaced by the raw sample covariance inside risk-aware action utility',
  'evidence_boundary':'deterministic synthetic sparse-covariance decision-loss shell; demonstrates mechanism and declared working/collapse regions only, not empirical forecasting or trading performance',
  'working_region':'declared covariance support is correct, training risk sample is small enough to contain off-support covariance noise, and risk-aware finite actions make that nuisance geometry decision-relevant',
  'collapse_regions':['risk_aversion = 0, where covariance leaves DLEW utility','fully dense support with shrinkage fixed at zero, where SACPS covariance equals raw covariance'],
  'failure_region':'support is externally declared; a held-out calibration sample that materially contradicts off-support independence triggers abstention rather than silent support learning',
  'result':working(),
  'dense_support_collapse':run(dense=True,support_limit=None),
  'zero_risk_collapse':run(risk_aversion=0.),
}
path=pathlib.Path(__file__).with_name('BENCHMARK_RESULT.json'); path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'gain':out['result']['validation_reference_regret_gain_vs_raw_covariance'],'candidate':out['result']['candidate_selected_model'],'control':out['result']['control_selected_model'],'dense_collapse':out['dense_support_collapse']['supported_equals_raw_covariance'],'zero_risk_parent':out['zero_risk_collapse']['parent_dlew_selected_model']},indent=2))
