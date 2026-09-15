import json
from test_reicapl import case
r=case(seed=0, adverse_shift=-.015)
out={
  'mechanism_removing_comparator':'same CAPL-style optimizer/data/random seed with uniform base asset caps; REIS consequence-aware selection does not alter the feasible set',
  'posterior_only_ablation':'same heterogeneous-cap mechanism but safeguards chosen by posterior probability only instead of posterior x consequence',
  'evidence_boundary':'synthetic regime-shift mechanism shell with caller-declared record-to-asset alignment; not empirical market validation and not a new-theory claim',
  'result':r.to_dict(),
}
open('BENCHMARK_RESULT.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
