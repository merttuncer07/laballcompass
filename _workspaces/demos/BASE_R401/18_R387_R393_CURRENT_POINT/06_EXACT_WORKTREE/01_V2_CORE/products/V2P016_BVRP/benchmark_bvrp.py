from bvrp import boundary_viability_plan as f
import json
from pathlib import Path
r=f(lower_action='reach',upper_action='avoid',nominal_action='reach',safe_fallback='hold').to_dict()
out={'model_version':'V2P016_BVRP_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
