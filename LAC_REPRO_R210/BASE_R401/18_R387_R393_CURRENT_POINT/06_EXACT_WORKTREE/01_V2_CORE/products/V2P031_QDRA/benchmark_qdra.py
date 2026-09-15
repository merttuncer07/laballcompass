import json
from pathlib import Path
from qdra import *
from qdra import ResolutionOption
regs=[ValidityRegion('near_boundary',.049,.0004,.05,5),ValidityRegion('far_high_raw_consequence',.005,.000025,.05,20)]
opts=[ResolutionOption('coarse',1,.5,.5),ResolutionOption('fine',3,.05,.05)]
r=quasineutral_decision_resolution(regs,opts,budget=4)
raw=AdaptiveConsequenceResolutionAllocator([DecisionRegion(x.name,x.time_importance,x.frequency_importance,x.consequence) for x in regs],opts).allocate(4)
out={'model_version':'V2P031_QDRA_V1','result':r.to_dict(),'mechanism_removing_comparator':raw,'control_allocation':{x['region']:x['option'] for x in raw['allocations']},'composed_allocation':{x['region']:x['option'] for x in r.allocation['allocations']},'evidence_boundary':'Gaussian validity-boundary weighting plus ACRA allocation on synthetic shell'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
