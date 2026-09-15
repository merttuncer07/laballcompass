import json
from pathlib import Path
from sarcp import support_adjusted_reserve, realized_shortfall
r=support_adjusted_reserve(mean_demand=100,nominal_sigma=10,ess_fraction=0.64,z=1.645,fragile_floor=.8)
d=122.0
out={'model_version':'V2P012_SARCP_V1','mechanism_removing_comparator':'variance-aware capacity reserve that ignores cohort-support erosion','result':r.to_dict(),'realized_demand':d,'nominal_shortfall':realized_shortfall(r.nominal_reserve,d),'support_adjusted_shortfall':realized_shortfall(r.support_adjusted_reserve,d),'evidence_boundary':'deterministic support-to-uncertainty routing benchmark only'}
Path(__file__).with_name('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
