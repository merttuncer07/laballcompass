from test_cdtdlew import case
import json
r=case(); open('BENCHMARK_RESULT.json','w').write(json.dumps({'mechanism_removing_comparator':'ordinary DLEW selection at the nominal channel regime only','evidence_boundary':'synthetic declared channel grid; no extrapolation beyond CDTS grid or empirical channel model','result':r},indent=2)); print(json.dumps(r,indent=2))
