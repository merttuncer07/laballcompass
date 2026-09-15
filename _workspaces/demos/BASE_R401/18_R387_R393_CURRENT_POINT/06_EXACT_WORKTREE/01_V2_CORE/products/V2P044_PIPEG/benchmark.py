
from test_pipeg import case
import json
r=case()
out={'mechanism_removing_comparator':'same BPISD persuasion solution and same information-production kernel, but policy selection ignores disclosure-induced change in future producer equilibrium','evidence_boundary':'synthetic two-state persuasion and three-producer equilibrium; declared mapping from channel TV to copy friction is a shell assumption, not an empirical law','result':r}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
