import json
from pathlib import Path
from bivcp import boundary_information_capacity_plan
k=dict(states=['low','high'],prior=[0.55,0.45],actions=['lean','reserve'],action_capacity={'lean':5,'reserve':10},action_cost={'lean':0,'reserve':2.5},demand={'low':5,'high':10},shortfall_penalty=2.0,channels={'probe':{'cost':0.4,'likelihood':{'L':{'low':0.9,'high':0.1},'H':{'low':0.1,'high':0.9}}}})
r=boundary_information_capacity_plan(**k)
out={'model_version':'V2P011_BIVCP_V1','mechanism_removing_comparator':'variance-aware capacity commitment without boundary-information acquisition','result':r.to_dict(),'expected_loss_reduction':r.baseline_loss-r.expected_total_loss,'evidence_boundary':'deterministic two-state decision-information benchmark only'}
Path(__file__).with_name('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
