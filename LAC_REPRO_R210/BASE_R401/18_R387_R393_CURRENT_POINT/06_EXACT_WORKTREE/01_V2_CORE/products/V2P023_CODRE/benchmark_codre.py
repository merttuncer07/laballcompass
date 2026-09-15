from codre import causal_overlap_explore as f
import json
from pathlib import Path
r=f(candidates=[('high_gain_low_overlap',10,.15),('moderate_supported',3,.8)],overlap_floor=.5).to_dict()
out={'model_version':'V2P023_CODRE_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
