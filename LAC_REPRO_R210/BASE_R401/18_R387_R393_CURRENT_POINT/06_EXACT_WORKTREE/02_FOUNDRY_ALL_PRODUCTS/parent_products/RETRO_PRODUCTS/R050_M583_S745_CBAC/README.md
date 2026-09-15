# CBAC v0.1 — Covariate-Balanced Assignment Certificate

CBAC generates fixed-size randomized treatment assignments, measures multivariate imbalance with a
covariance-aware Mahalanobis distance, forms a declared best-balance acceptance region, and randomly
selects one assignment from that region. It therefore improves pretreatment balance without replacing
randomization with a single deterministic optimum.

The certificate contains exact arm sizes, every standardized mean difference, maximum imbalance,
constant-covariate diagnostics, acceptance cutoff/percentile, and improvement over the first random
draw. Outcomes are not accepted as input, preventing direct outcome leakage into assignment.

CBAC is a standalone experiment and rollout-design product. It requires no current-product integration.

Run:

```powershell
python -m unittest -v test_cbac.py
python demo_balanced_assignment.py
```
