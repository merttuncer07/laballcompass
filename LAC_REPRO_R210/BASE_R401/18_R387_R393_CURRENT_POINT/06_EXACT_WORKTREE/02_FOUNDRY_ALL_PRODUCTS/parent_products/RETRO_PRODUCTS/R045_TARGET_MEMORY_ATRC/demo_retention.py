import json, numpy as np
from atrc import control_memory_retention
rng=np.random.default_rng(45); n=240; categories=np.arange(n)%12; categories[categories>1]=0
x=np.column_stack((categories==0,categories==1,np.sin(np.arange(n)/20)))
y=np.where(categories==1,5.0,1.0+.4*np.sin(np.arange(n)/20))+rng.normal(0,.05,n)
r=control_memory_retention(x,y,memory_budget=10,audit_horizon=30,neighbors=2,age_penalty=1e-5)
print(json.dumps({"target_aware_rmse":r.target_aware_rmse,"fifo_rmse":r.fifo_rmse,
"reservoir_rmse":r.reservoir_rmse,"improvement_vs_fifo":r.improvement_vs_fifo,
"retained_indices":r.retained_indices,"evictions":len(r.evictions),
"maximum_memory":r.maximum_realized_memory,"budget_violations":r.budget_violations,"status":r.status},indent=2))
