import json
from pathlib import Path
from istaicc import *
r=tipping_aware_information_acquisition([Channel('trigger',.04,.08,.02),Channel('myopic',.06,.04,.4)],base_friction=.4,network_strength=.9,temperature=.08,future_opportunity_value=.5)
out={'model_version':'V2P035_ISTAICC_V1','result':r.to_dict(),'mechanism_removing_comparator':{'immediate_choice':r.immediate_choice,'immediate_net_scores':{'trigger':.04-.08,'myopic':.06-.04}},'evidence_boundary':'stylized participation fixed-point and continuation-value mechanism shell only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
