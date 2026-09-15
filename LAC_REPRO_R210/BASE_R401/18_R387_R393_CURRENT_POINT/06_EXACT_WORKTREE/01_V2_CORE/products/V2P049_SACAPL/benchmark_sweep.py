import json
import numpy as np
from test_sacapl import _dataset, CAPL, SACPS
from sacapl import support_covariance_aware_policy

rows=[]
for rho in (0.0,0.25,0.5,0.7,0.85,0.95):
    risk, train_x, train_r, val_x, val_r = _dataset(spurious_correlation=rho)
    result = support_covariance_aware_policy(
        CAPL, SACPS.estimate_support_aware_covariance,
        train_x, train_r, val_x, val_r, risk, np.eye(4,dtype=bool),
        shrinkage_grid=[0.0], maximum_asset_weight=0.8, maximum_turnover=0.8,
        risk_aversion=20.0, transaction_cost=0.0002,
        population_size=30, generations=10, elite_fraction=0.15, seed=3,
    )
    rows.append({
        'declared_spurious_correlation':rho,
        'raw_off_support_max_abs_covariance':result['raw_off_support_max_abs_covariance'],
        'validation_ce_gain_vs_raw':result['validation_certainty_equivalent_gain_vs_raw_covariance'],
        'validation_variance_change_fraction_vs_raw':result['validation_variance_change_fraction_vs_raw_covariance'],
        'status':result['status'],
    })
out={
    'interpretation':'mechanism value rises in this deterministic shell as off-support nuisance covariance strengthens; this is a synthetic sensitivity surface, not empirical transfer evidence',
    'rows':rows,
}
with open('BENCHMARK_SWEEP_RESULT.json','w',encoding='utf-8') as f: json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
