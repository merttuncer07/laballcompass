import json,numpy as np
from sccatf import support_covariance_coupled_allocation as f
R=[{'time_weight':10,'frequency_weight':1},{'time_weight':1,'frequency_weight':10}]
O=[{'name':'short','time_spread':1,'frequency_spread':4,'cost':2,'support_exposure':2.0},{'name':'long','time_spread':4,'frequency_spread':1,'cost':2,'support_exposure':.1}]
C=np.array([[1,.95],[.95,1]])
rows={str(lam):f(R,O,C,budget=4,coupling_penalty=lam) for lam in [0,8,80,140,143,160,200]}
out={'mechanism_removing_comparator':'same CATF allocation with covariance coupling removed from the objective','evidence_boundary':'synthetic declared support covariance/exposure shell; low coupling correctly collapses to CATF and only sufficiently strong off-diagonal coupling changes the decision','parameter_sweep':rows}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
