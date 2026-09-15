# P003 result — SANP v0.1

Promotion state: **WORKING_COMPOSITION / SYNTHETIC_BENCHMARK**.

Primary fixed-seed synthetic benchmark:

- train / covariance-validation / fresh = 35 / 150 / 5000 observations;
- SACPS selected shrinkage = 0.25;
- raw sample covariance condition number = 9.2716;
- structured covariance condition number = 4.3031;
- ENPC with raw covariance fresh variance = 0.0001534922;
- SANP fresh variance = 0.0001241002;
- fresh variance reduction vs raw-covariance ENPC = **19.15%**;
- SANP factor exposure residual ≈ 1.2e-15 and all bounds hold;
- SACPS native minimum-variance weights had factor exposure -0.07179, showing the added constraint capability is nontrivial.

Adversarial support-misspecification benchmark:

- correct support fresh variance = 0.0001178985;
- wrong diagonal support fresh variance = 0.0001529528;
- raw-covariance ENPC fresh variance = 0.0001216791;
- wrong support is **25.70% worse** than raw ENPC and **29.73% worse** than correct support.

Interpretation: support-aware regularization can improve a constrained downstream decision, but the support assumption remains an external scientific/modeling claim. Numerical compliance is not evidence that the support graph is true.

Evidence label: **synthetic fixed-seed benchmark, not real-world proof**.
