from ccdre import conservation_calibrated_explore as f
import json
from pathlib import Path
r=f(channels=[('high_info',9,.4),('conserved',5,.02)],residual_limit=.05).to_dict()
out={'model_version':'V2P017_CCDRE_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
