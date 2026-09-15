import json
from pathlib import Path
from dwpcft import *
pts=[Point(.05,10,4,.01),Point(.1,1,4,.01),Point(.2,10,4,.5)]
r=decision_weighted_pcft_calibration(pts,additional_samples=12)
out={'model_version':'V2P037_DWPCFT_V1','result':r.to_dict(),'mechanism_removing_comparator':'uniform calibration allocation','evidence_boundary':'separable inverse-sqrt calibration-uncertainty mechanism shell only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
