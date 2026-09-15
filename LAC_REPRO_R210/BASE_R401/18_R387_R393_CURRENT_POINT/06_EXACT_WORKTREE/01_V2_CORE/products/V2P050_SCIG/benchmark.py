import json
from test_scig import case
out={
 'mechanism_removing_comparator':'same CSID failures, safeguard costs, coverage, budget and declared evidence-family labels with SACPS covariance dependence merging removed',
 'evidence_boundary':'synthetic safeguard-evidence residual shell; demonstrates dependence-partition correction, not empirical contract-loss calibration',
 'working_region':'nominally distinct evidence families share a strong supported dependence channel that makes CSID independence multiplication optimistic',
 'failure_region':'dependence threshold is calibration-sensitive and support remains externally declared; near-threshold cross-family correlations trigger abstention',
 'result':case(True),
 'collapse_result':case(False),
}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
