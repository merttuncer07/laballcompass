# Value-first benchmark batch 21

## RX-154 — DecisionSufficientCompressor
Equal 4-bit representations. Full-state 16-centroid KMeans compression yields median downstream
decision cost .9711; target-sufficient 16-bin compression .6134 (-36.8%). Log-loss .6420 -> .4403.
When reconstruction variance and decision information are aligned, cost gap is only .3%. Promote.

## RX-061 — CertificateVerifier
A degenerate nonoptimal KKT point passes first-order feasibility/stationarity/complementarity 100%
of the time. Adding active-set geometry/CQ and curvature precondition checks rejects it 100%, while
regular convex valid certificates remain accepted 100%. Strong assurance result; merge into
SolverCertificateAuditV0.

## RH-002 — MechanismDiscriminator
r01 was invalid because source fit already separated X from proxy W. Corrected r02 makes them exactly
source-equivalent. Source-only selection is ~49.1%; environment-invariance selection is 100%.
Choosing the broken proxy costs median +10.35 target MSE. Stable-proxy control returns discrimination
to chance. Merge into causal/invariance validation.

## RX-105 — ClockStateSelector
Dual-clock state is valid but incremental value is small: held-out log-loss .19454 vs best
single-clock .19722, only 1.36% improvement. Correct single-clock controls show negligible harm.
Keep as forecasting component, not standalone product.

## RX-107 — CandidateSetDecoder
r01/r02 exposed a benchmark bug: random codebooks contained duplicate codewords. Corrected r03 uses
64 unique codewords. At moderate ambiguity, point accuracy is 78.92%; a 95%-posterior list covers
97.5% with median size 2. In the clear unique-recovery shell, point accuracy is 100% and list size 1.
Under severe ambiguity, median list size honestly expands to 16. Promote.
