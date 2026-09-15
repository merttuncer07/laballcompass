# R-036 product result — DFDPE v0.1

**Product route:** standalone differentiation-free dynamic parameter estimator  
**Result:** working product; 4/4 focused tests pass

DFDPE implements the historical primitive “move the hard operation off the data.” It replaces
pointwise numerical differentiation with overlapping integral equations, checks whether the input
contains enough excitation to distinguish all parameters, and validates the resulting dynamics by
forward simulation on an untouched input path.

The finite-difference estimate is retained as a comparison, not as a gate. Prior-art overlap remains
attached as provenance and does not prevent practical use.

In the first noisy construction, the true parameters `(-0.42, 1.35, 0.22)` were recovered as
`(-0.43103, 1.37115, 0.22918)` from 73 overlapping integral windows. On a wholly different input
path, rollout RMSE was 0.01559 versus 0.02594 for the numerical-derivative baseline: a 39.91%
reduction. The window design had full rank and condition number 5.72. A constant-output/constant-input
construction returned `UNDEREXCITED_PARAMETERS_NOT_IDENTIFIABLE` rather than fabricated estimates.
