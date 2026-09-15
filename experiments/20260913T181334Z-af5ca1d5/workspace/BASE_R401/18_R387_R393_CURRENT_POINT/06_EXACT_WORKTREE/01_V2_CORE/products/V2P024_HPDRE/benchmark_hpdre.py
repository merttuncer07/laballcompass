from hpdre import hidden_population_explore as f
import json
from pathlib import Path
r=f(action_margin=.08,hidden_mass=.12,max_effect_per_mass=1).to_dict()
out={'model_version':'V2P024_HPDRE_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
