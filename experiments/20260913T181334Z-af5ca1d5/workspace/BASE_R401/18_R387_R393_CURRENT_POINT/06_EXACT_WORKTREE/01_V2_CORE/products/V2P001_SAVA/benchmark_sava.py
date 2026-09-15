import json
from pathlib import Path
from sava import AuditCandidate,allocate_verification_liquidity


candidates=[AuditCandidate('A_large_suspicious',1.,(60,0)),AuditCandidate('B_clean_shared',1.,(60,40)),AuditCandidate('C_clean_anchor',1.,(0,40))]
scenarios=[(.70,set()),(.25,{'A_large_suspicious'}),(.05,{'B_clean_shared'})]
exact=allocate_verification_liquidity(candidates,(60,40),scenarios,audit_slots=1)
scalable=allocate_verification_liquidity(candidates,(60,40),scenarios)
result={
 'exact_one_slot':exact.to_dict(),
 'scalable_allocation':scalable.to_dict(),
 'naive_minus_shared_capacity_value':scalable.naive_independent_value-scalable.expected_deployable_liquidity,
 'relative_double_count_removed':scalable.overlap_removed_value/scalable.naive_independent_value,
}
Path(__file__).with_name('BENCHMARK_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
