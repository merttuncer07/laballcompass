# P043 DABR v0.1 — Decision-Aware Balanced Reducer

## Composition
BRED → DLEW. BRED supplies stable reduced-order candidates; DLEW evaluates the downstream actions induced by those reduced outputs on protected episodes.

## Benchmark result
A 3-state / 2-output stable system was reduced under a generic BRED error budget of 0.5. Generic BRED accepted **order 1**. Decision-aware protected evaluation selected **order 2**. Validation decision regret fell from **0.0227174** to **0.0000970** (about **99.57% lower**) while the BRED theoretical error bound tightened from **0.47920** to **0.03390**.

## Claim boundary
The full model is the protected reference for this model-reduction audit; DABR does not prove that the full model is physically true.

Promotion state: **WORKING_COMPOSITION / SYNTHETIC DECISION BENCHMARK**.
