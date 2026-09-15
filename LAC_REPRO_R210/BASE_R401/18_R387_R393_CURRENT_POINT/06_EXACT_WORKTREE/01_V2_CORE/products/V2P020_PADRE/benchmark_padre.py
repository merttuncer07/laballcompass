from padre import privacy_accuracy_explore as f
import json
from pathlib import Path
r=f(epsilon=.5,margin=1,sensitivity=1,target=.9,channel='private_probe').to_dict()
out={'model_version':'V2P020_PADRE_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
