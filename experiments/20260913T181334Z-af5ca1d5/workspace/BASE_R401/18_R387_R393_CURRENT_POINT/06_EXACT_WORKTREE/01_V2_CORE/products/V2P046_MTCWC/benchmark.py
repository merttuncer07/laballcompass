
from test_mtcwc import case
import json
r=case(); out={'mechanism_removing_comparator':'same residual stream, same CWC gains and frozen base-scale; MCST tipping signal and state reset removed','evidence_boundary':'synthetic Gaussian residual shell with externally observed stress parameter; demonstrates reset coupling only, not a general change-point or conformal-coverage theorem','result':r}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
