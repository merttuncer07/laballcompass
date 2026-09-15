# R-048 product result — MBPF v0.1

**Product route:** standalone burnout-adjusted prepayment forecaster  
**Result:** working product; 4/4 tests pass

MBPF evolves latent propensity classes separately, allowing high-propensity borrowers to leave the
pool faster. The surviving mixture therefore changes endogenously instead of being forced to retain
the initial average prepayment propensity.

In the first 20,000-loan, 72-month construction, effective monthly prepayment fell from 2.406% to
0.986% and surviving average propensity fell from 0.9625 to 0.3918. MBPF forecast 12,500.3 cumulative
prepayments; the homogeneous-pool calculation predicted 15,908.6, overestimating exits by 27.27%.
Competing defaults and exact cohort mass are retained.

Positive-control provenance is not a product veto; servicing and duration planning can use MBPF now.
