# P041 DDER v0.1 — Double-Diffusive Exposure Resilience

## Capability

DDER composes UTDIM's unequal-transport instability detector with HMRM's exposure-and-recovery logic. UTDIM answers whether a transport-mismatch mode grows; DDER additionally asks whether the currently excited fastest mode has enough consequence-bearing exposure to matter operationally.

## Benchmark result

The benchmark is statically stable (`static_stability_index = 1`) yet UTDIM finds unequal-transport destabilization: maximum growth is positive while the equal-diffusivity counterfactual at the fastest mode is stable. Sampling that fastest mode at Δt=0.25 yields a multiplier above 1. With current mode amplitude **0.2**, HMRM sees material exposure and non-recovery, so DDER raises an exposure-qualified instability alert. With the identical physical instability but amplitude **0.001**, the alert is suppressed because current consequence-bearing exposure is below threshold.

## Claim boundary

DDER uses only UTDIM's fastest scalar growth rate. It does not reconstruct the full signed eigenvector or replace the underlying multi-field stability model. Current modal amplitude and consequence gain are explicit external measurements/assumptions.

## Verification

5/5 product tests pass.
