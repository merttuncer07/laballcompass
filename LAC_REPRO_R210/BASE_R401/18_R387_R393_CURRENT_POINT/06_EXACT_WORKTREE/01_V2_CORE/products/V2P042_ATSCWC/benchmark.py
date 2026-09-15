
from test_atscwc import case
import json
r=case()
out={'mechanism_removing_comparator':'same CWC and same query budget with ActiveThresholdSensing selection replaced by a frozen evenly-spaced query schedule','evidence_boundary':'synthetic repeated threshold-localization tasks with declared binary response accuracy; demonstrates closed-loop mechanism only, not deployment calibration','result':r}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
