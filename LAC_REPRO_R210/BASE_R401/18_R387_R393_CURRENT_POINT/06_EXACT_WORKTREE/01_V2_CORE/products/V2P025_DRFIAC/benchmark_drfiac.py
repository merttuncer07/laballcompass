from drfiac import decision_relevant_firewall as f
import json
from pathlib import Path
r=f(channels=[('contaminated_high_value',10,True),('clean_decision_relevant',4,False)]).to_dict()
out={'model_version':'V2P025_DRFIAC_V1','result':r,'evidence_boundary':'deterministic synthetic mechanism benchmark only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
