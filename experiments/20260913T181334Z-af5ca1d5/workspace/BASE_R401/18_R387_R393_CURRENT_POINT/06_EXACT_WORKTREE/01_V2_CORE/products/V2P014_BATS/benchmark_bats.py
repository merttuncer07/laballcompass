from bats import boundary_aware_timing as f
import json
from pathlib import Path
r=f(lower_action=1,upper_action=1,timing_candidates=[(1,.5),(2,.2)],budget=1).to_dict()
out={'model_version':'V2P014_BATS_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
