from bgtw import boundary_gated_wealth as f
import json
from pathlib import Path
r=f(wealth=10,price=2,lower_action=1,upper_action=1).to_dict()
out={'model_version':'V2P015_BGTW_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
