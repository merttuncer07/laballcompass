from stha import support_tipped_holdout as f
import json
from pathlib import Path
r=f(losses={'aggressive':.01,'robust':.03},ess_fraction=.42,support_floor=.6).to_dict()
out={'model_version':'V2P019_STHA_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
