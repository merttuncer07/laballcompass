# V2P034 SCOPG — Support-Constrained Observation-Policy Guard

K081 removes passive-state confounding before estimating measurement-policy backaction, but the regression can still be numerically identified by a handful of effectively weighted observations. SCOPG adds SACPS-style support geometry: effective sample size and the weighted design covariance must both be adequate before the policy coefficient is emitted.

The result fails closed under poor overlap or near-collinearity. It is a synthetic linear mechanism benchmark, not a general causal-identification theorem.
