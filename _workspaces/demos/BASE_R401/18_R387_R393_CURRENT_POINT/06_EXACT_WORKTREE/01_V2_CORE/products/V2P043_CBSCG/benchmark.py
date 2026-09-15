
from test_cbscg import case
import json
r=case()
out={'mechanism_removing_comparator':'same Wardrop strategic-response project choice using midpoint demand with the CBIA information-acquisition step removed','evidence_boundary':'synthetic two-project affine Wardrop network; demand prior and measurement cost declared; no transport-demand calibration claim','result':r}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
