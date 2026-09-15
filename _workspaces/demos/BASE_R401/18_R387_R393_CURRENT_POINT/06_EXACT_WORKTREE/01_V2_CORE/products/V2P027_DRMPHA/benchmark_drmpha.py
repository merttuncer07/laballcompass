from drmpha import decision_relevant_holdout_audit as f
import json
from pathlib import Path
r=f(development_scores={'aggressive':3,'robust':1},protected_losses={'aggressive':.08,'robust':.01}).to_dict()
out={'model_version':'V2P027_DRMPHA_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
