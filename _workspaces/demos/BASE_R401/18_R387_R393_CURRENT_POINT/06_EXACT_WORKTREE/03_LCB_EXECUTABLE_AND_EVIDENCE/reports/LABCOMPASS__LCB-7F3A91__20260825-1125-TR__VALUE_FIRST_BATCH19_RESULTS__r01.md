# Value-first benchmark batch 19

## RH-010 — ObservationPolicyConfoundingGuard
Ordinary proxy adjustment r01 still left confounding. Structural r02 uses the observation policy
itself as information about latent state. True backaction is -.85; naive regression estimates +.056
(abs error .906), while the policy-aware model estimates -.851 (error .00593; ~99.35% reduction).
Random-policy control makes both approaches essentially unbiased. Promote as a joint monitoring-policy/backaction core.

## RX-020 — MicroMemoryDiagnostic
Symmetric initial directions erase population signed direction. Persistent-vs-weak memory AUC is
.780 for absolute macro projection, .219 for trajectory variance, and .9997 for directional
micro-autocorrelation. Weak-memory control falls to .691. Promote as a diagnostic core.

## RX-118 — EventInnovationSensor
r01 improved hidden-state AUC .666 -> .773 but narrowly missed the first superiority gate. In the
strong-seasonality shell, raw event-count AUC .643 vs expected-intensity innovation .801 (+.158).
Constant-intensity control is identical .779/.779. Strong shell-specific result; merge into
ObservationTimingSensor as compensator/innovation logic.

## RX-090 — LoadAwareConnectivity
All graphs are physically connected. Under capacity stress, feasibility accuracy is 61.2% for
physical connectivity, 49.2% for widest single path, and 100% for multi-route max flow. Low-demand
control makes topology sufficient again. Merge into ResilientFlowRouter/shared-capacity family.

## RX-015 — ValidatorNotTruthOracle
A single biased/noisy reference selects the true numerical-RMSE winner only 10.6% of tasks; symmetric
two-reference agreement reaches 39.7% (+29.1pp), narrowly below the predeclared +30pp new-core gate.
Ranking winner and numerical winner disagree in 100% of tasks. Keep as QA/reporting component, not a
new standalone core.
