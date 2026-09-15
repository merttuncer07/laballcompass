import json
from pathlib import Path
from spitwmr import search_policy_targeted_reduction as f
r=f([[.95,0,0],[0,.8,0],[0,0,.6]],[[10],[1],[1]],['energy','policy','minor'],policy_sensitivity=[0,5,.1],retain_count=1,horizon=15)
out={'model_version':'V2P032_SPITWMR_V1','result':r.to_dict(),'mechanism_removing_comparator':'TWMR energy baseline with no search-policy target','evidence_boundary':'linear-system synthetic mechanism shell only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
