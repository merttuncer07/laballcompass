import json
from pathlib import Path
from vcmf import viability_constrained_multifidelity as f
r=f(budget=10,fine_cost=5,cheap_cost=1,fine_variance=.04,cheap_variance=.09,cheap_bias_bound=.5,viability_margin=.1,min_fine=1)
out={'model_version':'V2P033_VCMF_V1','result':r.to_dict(),'mechanism_removing_comparator':{'unconstrained_choice':r.unconstrained_choice,'unconstrained_worst_case_bias':r.unconstrained_worst_case_bias},'evidence_boundary':'bounded-bias multifidelity estimator under declared viability margin only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
