import json
from pathlib import Path
from bosaro import support_aware_robust_optimizer as f
r=f([.12,.10],[1,0],base_shift_radius=.02,support_fraction=.25,risk_penalty=.001,grid_step=.002)
out={'model_version':'V2P038_BOSARO_V1','result':r.to_dict(),'mechanism_removing_comparator':'same directional robust optimizer with support fraction fixed to 1','evidence_boundary':'two-action simplex synthetic robust-optimization shell only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
