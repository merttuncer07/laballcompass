import json
from pathlib import Path
from susca import Item,support_adjusted_shared_capacity as f
items=[Item('fragile_high_nominal',10,(10,0),.2),Item('supported_overlap',7,(10,5),1),Item('anchor',3,(0,5),1)]
r=f(items,(10,5),min_support=.3)
blind=f([Item(x.name,x.nominal_value,x.pool_contributions,1) for x in items],(10,5),min_support=.3)
true_support={x.name:x.support_fraction for x in items}; true_value={x.name:x.nominal_value for x in items}
def realized(alloc): return sum(alloc[n]*true_value[n]*true_support[n] for n in alloc)
out={'model_version':'V2P029_SUSCA_V1','mechanism_removing_comparator':blind.to_dict(),'support_aware':r.to_dict(),'control_realized_supported_value':realized(blind.allocation),'composed_realized_supported_value':realized(r.allocation),'realized_gain':realized(r.allocation)-realized(blind.allocation),'evidence_boundary':'deterministic support-and-polymatroid mechanism shell only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2))
