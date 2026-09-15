import json, statistics
from test_reicapl import case
shifts=[-.002,-.005,-.010,-.015,-.020]
rows=[]
for shift in shifts:
    gains=[]; posterior=[]
    for seed in range(3):
        r=case(seed=seed,adverse_shift=shift)
        gains.append(r.gain_vs_removed_mechanism); posterior.append(r.gain_vs_posterior_only)
    rows.append({
      'adverse_shift':shift,
      'seeds':3,
      'mean_gain_vs_removed':statistics.mean(gains),
      'positive_gain_cases':sum(x>0 for x in gains),
      'mean_gain_vs_posterior_only':statistics.mean(posterior),
      'positive_vs_posterior_cases':sum(x>0 for x in posterior),
      'gains_vs_removed':gains,
    })
out={
  'rows':rows,
  'interpretation':'benefit is conditional: benign/small shift can make the tighter REIS-selected cap harmful; sufficiently adverse aligned shift creates a working region. No universal superiority claim.',
  'working_region_rule':'in this declared synthetic shell, -0.010 or more adverse B shift should show majority-positive removal-control gain; -0.015 and -0.020 are expected 3/3 positive in the frozen sweep.',
}
open('BENCHMARK_SWEEP_RESULT.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
