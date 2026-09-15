from bmdre import belief_metric_explore as f
import json
from pathlib import Path
r=f(tipping_distance=.03,approximation_error=.05).to_dict()
out={'model_version':'V2P021_BMDRE_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
