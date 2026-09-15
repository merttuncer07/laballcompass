from drsvco import decision_relevant_cycle_explore as f
import json
from pathlib import Path
r=f(points=[('static_optimum',10,.9,.01),('state_boundary',5,.28,.08)],min_active=.25).to_dict()
out={'model_version':'V2P026_DRSVCO_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
