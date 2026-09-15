# Observed dependency problem in EBC — 2026-09-14

The local implementation added `maximum_power * compatibility / SE^2` once per historical record and only required distinct display names. The cap limited total nominal precision but did not preserve the mean or variance when the same observation was repeated under new names. Actual reproduction is in examples/borrowing/result.json.

The repair addresses declared aliases of a single normal estimate, including copies of the current observation. It does not treat a common organization, study or workbook as proof of perfect statistical dependence. Partial overlap between different estimates remains outside this independent-observation EBC model.

Primary comparison: metafor's vcalc interface and implementation expose clustering, observation/construct identities, correlations, and shared comparison groups separately. This supports distinguishing identical observations from partially overlapping estimates rather than collapsing an entire source indiscriminately:
- https://wviechtb.github.io/metafor/reference/vcalc.html
- https://github.com/wviechtb/metafor/blob/master/R/vcalc.r

Cochrane's description of shared comparators also identifies reuse of the same participants as a unit-of-analysis error caused by unaddressed correlation, rather than additional independent evidence:
- https://training.cochrane.org/handbook/current/chapter-23

Verification uses an independent closed-form normal combination and a GLS pseudoinverse of an explicitly perfect within-observation covariance matrix, with EBC's adaptive powers held fixed. It does not reproduce a full metafor fit, demonstrate general covariance handling, or validate frequentist coverage after adaptive weighting. No performance or novelty advantage is claimed.


## Explicit joint covariance extension

`borrow_correlated_evidence` now accepts covariance aligned by exact observation names, including correlations with the current estimate. Declared exact aliases still coalesce; their covariance rows must agree. Singular/ill-conditioned residual covariance after alias removal is rejected rather than made positive definite by changing the model. Distinct estimates must concern a common scalar estimand. Source identity is not inferred from content similarity.

For current value x with variance v, historical values h with covariance H, and current/history covariance c, use gamma=c/v, z=h-gamma*x, a=1-gamma and S=H-c*c.T/v. Given the current value, z has mean a*mu and covariance S. With declared/compatibility powers D, conditional precision is P=sqrt(D)*solve(S,sqrt(D)); added information is a.T*P*a. A scalar cap multiplies this conditional information. Current information 1/v is added once. Full powers and an inactive cap recover GLS on the original joint covariance. This conditional construction also explains why current/history correlation cannot be fixed solely by changing history/history precision.

The diagonal-power tempering policy is explicit. Adaptive powers and estimated covariance are treated as fixed in reported model intervals; their nominal coverage is not validated. Negative GLS coefficients are possible and are retained. General dependence among REL's distinct consistency tests is still not modeled by this extension.

Independent references actually reproduced:
- 56 study rows in 11 districts, from the official metadat table (numeric transcription recorded in examples/correlated-evidence/SOURCES.json). Published fitted variance components 0.0651 and 0.0327 are held fixed; no REML refit. Joint estimate 0.18472238, SE 0.08457226, compared with the published 0.1847132 / rounded 0.0846 and an independent inverse-matrix GLS result. Ignoring off-diagonal covariance yields 0.12759697 / SE 0.04580421. The tiny difference from the published joint estimate follows use of rounded variance components.
- Shared-control arithmetic from the first displayed Lecrubier 1997 row of dat.linde2015: log-odds contrast covariance follows A*Sigma*A.T. The variance of their difference is 0.131091924, matching direct calculation from the two treatment arms. A diagonal-only calculation gives 0.244187162 because it fails to cancel the reused control term. The two treatment effects are not pooled as one estimand, and no clinical inference is made.

This extends the lab's numerical capability and passes the reference calculations. It does not establish a new statistical method or end-user audit effectiveness.
