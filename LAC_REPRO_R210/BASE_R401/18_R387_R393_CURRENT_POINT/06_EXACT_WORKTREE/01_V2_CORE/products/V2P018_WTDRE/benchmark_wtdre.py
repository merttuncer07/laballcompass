from wtdre import wasserstein_tipped_explore as f
import json
from pathlib import Path
r=f(candidates=[('high_variance',.8,1),('near_flip',.12,1)],max_distance=1).to_dict()
out={'model_version':'V2P018_WTDRE_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
