# Value-first benchmark batch 5

## RH-004 — ValueOfInformationActiveSensing
Ordered-threshold fault/location sensing with 32 possible locations and 5 noisy tests.
Strong static prior-quantile design exact accuracy 13.7%; adaptive posterior-geometry design
55.5%. Mean absolute location error 3.49 -> 1.83. At 80% and 97% sensor accuracy the adaptive
advantage persists. With one measurement the two policies are identical. Promote.

## RH-006 — EffectiveRedundancyGuard
r01 showed cheap escalation could help even without common mode, so r02 priced escalation explicitly.
At escalation cost 5: common-mode homogeneous architecture decision cost 8.01 vs diverse backstop
1.87. Under independent errors the ordering reverses: .448 vs .672. Common-mode break-even
escalation cost ~39; independent-error break-even ~3.19. Promote as common-mode gated architecture.

## RX-035 — DesignAwareInference
Eight-pair design-aware exact test has 5.2% null rejection at alpha=.05. Wrong complete-randomization
reference is overconservative (0%). Under a true effect=1, design-aware power is 99.6% vs 0% under
the wrong reference. Same final table example: p=.0078 under paired assignment vs .916 under complete
randomization. Promote.

## RX-057 — ReachableSubspaceAudit
All eight states are perfectly observable. Sensor-rank heuristic falsely promises feasibility in
50.5% of rank-deficient cases; simple target-count/control-rank condition still false-promises 12.6%.
Projection onto the actual finite-horizon reachable subspace is 100% correct. Full-controllability
control makes all methods agree. Promote.

## RX-030 — SpectralRelationGate
r02 uses a quadrature narrow-band relation so zero-lag correlation is genuinely absent.
At n=8192: raw single-bin power 10.7%, Welch-smoothed band coherence 100%, time-domain correlation
5.7%. Null Welch rejection remains ~3.7–7.0%. Broadband relation control is detected by simple
time-domain correlation. Promote as a band-specific relation component.
