from test_bmcapl import case
import json
r=case(0); open('BENCHMARK_RESULT.json','w').write(json.dumps({'mechanism_removing_comparator':'same CAPL shell with fixed base turnover independent of BMDT tipping distance','evidence_boundary':'synthetic regime-shift mechanism shell; BMDT-to-turnover mapping is declared, not empirically calibrated','result':r},indent=2)); print(json.dumps(r,indent=2))
