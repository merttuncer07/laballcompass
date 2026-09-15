# P016 CATR v0.1 — Calibration-Aware Trigger Router

## Composition

CWC -> prequential interval upper endpoint -> DTTC candidate-signal competition.

CATR never equates interval width with the protected event. The raw forecast center and the CWC upper endpoint are separate trigger candidates. DTTC chooses the signal/threshold using explicit false-negative and false-positive costs. The chosen signal and threshold are then frozen for a fresh sequential segment; CWC may continue to update only from outcomes already observed.

## Benchmark

Synthetic 3,000-step forecast stream. Thirty percent of cases have higher declared uncertainty and scale-linked conservative underprediction. First 2,000 observations design the trigger; last 1,000 are fresh prequential evaluation.

See `BENCHMARK_RESULT.json` for exact metrics. The calibrated endpoint is selected in this regime and materially lowers fresh weighted trigger loss versus the center-only trigger. A separate unit test with zero-width/no-extra-information endpoints selects the center, demonstrating that uncertainty is not forced into the decision.

## Claim boundary

The benchmark is prequential, not a frozen-feature i.i.d. holdout: later fresh CWC features may use earlier fresh outcomes, never the current or future outcome. CATR does not claim that an upper endpoint is universally superior; DTTC is explicitly allowed to reject it.
