import json
from cpdbe import Edge, pressure_guided_deployable_tipping

edges=[Edge('s0',200),Edge('s1',150),Edge('b',40),Edge('s2',120),Edge('s3',200)]
grid={e.name:[e.capacity+10,e.capacity+20,e.capacity+40,e.capacity+80] for e in edges}
r=pressure_guided_deployable_tipping(100,edges,horizon=1,target=70,capacity_grid=grid)
print(json.dumps({"model_version":"V2P007_CPDBE_DEV_V1",**r.to_dict()},indent=2))
