
from test_fptwc import case
import json
r=case()
out={'mechanism_removing_comparator':'same p-value stream, alpha budget, and TestingWealthController; FPTE tipping proximity is removed so gamma profile remains baseline','evidence_boundary':'synthetic early-signal sequential-testing shell; demonstrates timing-coupling mechanism, not FDR validity outside the controller assumptions','result':r}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
