import json
from pathlib import Path
from pcfmcsc import closure_fidelity_monotonicity as f
r=f([0,.05,.1,.2,.5],[.08,.07,-.15,-.05,-.3])
out={'model_version':'V2P036_PCFMCSC_V1','result':r.to_dict(),'mechanism_removing_comparator':{'assumption':'after first negative margin, all larger tolerances remain unsafe','first_negative_tolerance':0.1,'contradicted_by_later_margin':{'tolerance':0.2,'margin':-0.05,'direction_recovery':True}},'evidence_boundary':'finite ordered tolerance-grid structural audit only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
