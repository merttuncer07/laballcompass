import json
from pathlib import Path
import numpy as np
from scspia import InformationChannel, acquire_for_search_policy, simplex_tangent_basis, support_calibrated_search_policy_acquisition

rng = np.random.default_rng(1)
B = simplex_tangent_basis(8)
variances = np.exp(rng.uniform(np.log(0.0002), np.log(0.006), 7))
Ctrue_z = np.diag(variances)
Ctrue = B @ Ctrue_z @ B.T
uniform = np.ones(8) / 8
Z = rng.multivariate_normal(np.zeros(7), Ctrue_z, size=12)
X = uniform + Z @ B.T
mean = np.array([.12, 0, 0, .40, 0, .48, 0, 0], float)
policies = [('local', 8, 0), ('intermittent', 2, 3)]
channels = [InformationChannel(f'c{j}', B[:,j], .0004, .002) for j in range(7)]
oracle = acquire_for_search_policy(mean, Ctrue, policies=policies, channels=channels)
raw = acquire_for_search_policy(mean, np.cov(X,rowvar=False,ddof=1), policies=policies, channels=channels)
structured = support_calibrated_search_policy_acquisition(X, np.eye(7,dtype=bool), mean, policies=policies, channels=channels, shrinkage_grid=[0.0])

def vals(r):
    return {x['name']: x['net_value'] for x in r.ranked_channels}

o = vals(oracle); rr = vals(raw); ss = {x['name']: x['net_value'] for x in structured.ranked_channels}
result = {
    'model_version': 'V2P010_SCSPIA_DEV_V1',
    'mechanism_removing_comparator': 'P138 using unconstrained raw sample covariance',
    'true_tangent_variances': variances.tolist(),
    'oracle_chosen_channel': oracle.chosen_channel,
    'raw_sample_chosen_channel': raw.chosen_channel,
    'support_calibrated_chosen_channel': structured.chosen_channel,
    'oracle_top_net_value': o[oracle.chosen_channel],
    'raw_estimated_oracle_channel_net_value': rr[oracle.chosen_channel],
    'structured_estimated_oracle_channel_net_value': ss[oracle.chosen_channel],
    'raw_absolute_oracle_channel_value_error': abs(rr[oracle.chosen_channel]-o[oracle.chosen_channel]),
    'structured_absolute_oracle_channel_value_error': abs(ss[oracle.chosen_channel]-o[oracle.chosen_channel]),
    'structured': structured.to_dict(),
}
Path(__file__).with_name('BENCHMARK_RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
