# V2P051 SACDLW — Support-Aware Covariance Decision-Loss Workbench

R037 SACPS composes with R044 DLEW by placing support-aware covariance directly inside DLEW's finite-action utility before action argmax and model-selection regret are computed. The removal control holds the DLEW shell fixed and restores raw sample covariance.

The target failure is not generic covariance estimation: it is a DLEW ranking/action error caused when finite-sample off-support covariance changes risk-aware downstream actions. Dense support with zero shrinkage collapses exactly to the raw-covariance control; zero risk aversion collapses to parent DLEW selection. Declared support remains external and can be contradicted by a held-out calibration guard, which abstains.

Status: **R390 shadow candidate. Not canonical.**
