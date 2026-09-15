from cfdre import closure_fidelity_explore as f
import json
from pathlib import Path
r=f(fidelity=.74,floor=.9).to_dict()
out={'model_version':'V2P022_CFDRE_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
