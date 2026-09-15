# V2P051 SACDLW — R390 shadow quality result

Status: **DISTINCT PRODUCT CANDIDATE; NOT CANONICAL**.

R037 SACPS is injected into R044 DLEW before finite-action argmax and regret evaluation. The support-aware covariance therefore changes action trajectories and can change which predictive model DLEW selects. The mechanism-removing control holds predictions, outcomes, action set, transaction cost, risk aversion and DLEW ranking logic fixed while replacing SACPS covariance with the raw sample covariance.

Deterministic working shell: 12/12 hardened tests pass. In the declared strong unsupported-covariance nuisance case, SACDLW selects `A_signal` while the raw-covariance control selects `B_stable`, with common-reference validation regret gain ≈ 0.00232. Dense support with zero shrinkage collapses exactly to the raw control. Risk aversion zero collapses to parent DLEW. A held-out calibration contradiction triggers abstention.

Sensitivity is explicitly non-universal: as the synthetic unsupported negative covariance becomes strong, mean regret gain becomes positive, but losing seeds remain. This is mechanics evidence only, not empirical superiority or a new-theory claim.
