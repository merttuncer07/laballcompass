import json
from pathlib import Path
from sgmb import _multifidelity_allocation, support_gated_multifidelity_monitoring

k = dict(
    cohort_size=10000,
    base_rates=[0.03] * 24,
    propensity_multipliers=[0.2, 1.0, 5.0],
    initial_class_weights=[0.3, 0.4, 0.3],
    month=24,
    total_budget=200.0,
    fine_cost=5.0,
    cheap_cost=1.0,
    pilot_correlation=0.95,
    min_fine=10,
    fragile_ess_fraction=0.8,
)
blind = _multifidelity_allocation(k['total_budget'], k['fine_cost'], k['cheap_cost'], k['pilot_correlation'], k['min_fine'])
guarded = support_gated_multifidelity_monitoring(**k)
result = {
    'model_version': 'V2P009_SGMB_DEV_V1',
    'mechanism_removing_comparator': 'K048 allocation using pilot correlation without BOSA support gate',
    'month': 24,
    'effective_sample_fraction': guarded.effective_sample_fraction,
    'support_status': guarded.support_status,
    'blind_k048': blind,
    'guarded': guarded.to_dict(),
    'unsupported_cheap_acquisitions_comparator': blind['n_cheap'] if guarded.support_status != 'SUPPORT_USABLE' else 0,
    'unsupported_cheap_acquisitions_guarded': guarded.n_cheap if guarded.support_status != 'SUPPORT_USABLE' else 0,
}
Path(__file__).with_name('BENCHMARK_RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
