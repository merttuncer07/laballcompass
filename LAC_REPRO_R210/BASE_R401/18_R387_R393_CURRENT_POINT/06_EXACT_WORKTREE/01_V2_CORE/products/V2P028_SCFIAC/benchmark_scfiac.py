from scfiac import support_constrained_firewall as f
import json
from pathlib import Path
r=f(channels=[('clean_unsupported',9,False,False),('suspect_supported',8,True,True),('safe_supported',4,False,True)]).to_dict()
out={'model_version':'V2P028_SCFIAC_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
