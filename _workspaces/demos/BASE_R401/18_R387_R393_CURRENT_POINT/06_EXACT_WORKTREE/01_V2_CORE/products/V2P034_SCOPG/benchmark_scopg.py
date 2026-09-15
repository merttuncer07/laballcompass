import json,numpy as np
from pathlib import Path
from scopg import support_constrained_policy_backaction as f
s=np.linspace(-1,1,20); p=(s>0).astype(float); y=2*s+.5*p
supported=f(y,p,s,np.ones(20)); w=np.full(20,1e-9); w[0]=1; fragile=f(y,p,s,w,min_ess_fraction=.2)
wn=w/w.sum(); X=np.column_stack([np.ones(len(y)),s,p]); unguarded=float((np.linalg.pinv(X.T@(wn[:,None]*X))@(X.T@(wn*y)))[2])
out={'model_version':'V2P034_SCOPG_V1','supported':supported.to_dict(),'fragile_support':fragile.to_dict(),'mechanism_removing_comparator':{'unguarded_fragile_policy_effect':unguarded},'evidence_boundary':'synthetic weighted linear backaction shell only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
