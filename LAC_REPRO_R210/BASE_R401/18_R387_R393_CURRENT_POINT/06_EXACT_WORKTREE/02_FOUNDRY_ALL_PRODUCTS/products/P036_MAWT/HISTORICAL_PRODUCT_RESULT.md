# P036 MAWT v0.1 — Mass-Aware Wasserstein Transport

## Capability

MAWT keeps two transport questions separate: WBDP measures **normalized shape displacement**, while UMCA accounts for **raw moved, created and destroyed mass**. It prevents normalized distribution geometry from silently erasing quantity changes.

## Benchmark result

The source contains 100 total units split 50/50 across positions 0 and 10. The target has the identical normalized 50/50 shape but 150 total units, split 75/75. WBDP therefore reports normalized W2 distance **0**. UMCA simultaneously reports **50 units of created mass**. The balanced normalization baseline rescales the source by **1.5** and reports zero creation, showing exactly what the normalized-only view hides.

A second adversarial test confirms the converse distinction: when total mass is equal but geometry shifts from position 0 to 10, W2 is 10; whether the operational plan physically moves mass or destroys/recreates it depends on the separately declared movement versus mass-change costs.

## Claim boundary

W2 and UMCA cost are not merged into one pseudo-metric. W2 answers normalized shape change; UMCA answers raw operational accounting under declared costs. The movement-cost power is an operator choice and does not alter WBDP's definition.

## Verification

5/5 product tests pass.
