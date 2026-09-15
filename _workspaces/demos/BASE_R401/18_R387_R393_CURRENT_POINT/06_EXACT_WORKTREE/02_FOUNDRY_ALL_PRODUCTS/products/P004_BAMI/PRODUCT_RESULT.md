# P004 result — BAMI v0.1

Promotion state: **WORKING_COMPOSITION / SYNTHETIC_DECISION_BENCHMARK**.

Tests: **6/6 passing**.

Primary 36-month fixed-parameter benchmark, 100,000-loan cohort:

- initial effective prepayment hazard = 0.033125;
- month-36 effective prepayment hazard = 0.0192499, demonstrating burnout/selection;
- homogeneous approximation keeps the initial 0.033125 rate constant;
- at $3,150 intervention cost per loan, homogeneous MCRIS net value = **$33.04M**;
- burnout-aware BAMI net value = **$56.00M**;
- BAMI therefore changes estimated net value by **+$22.96M** and estimates about **227.9 additional defaults avoided** relative to the homogeneous approximation.

Decision-flip benchmark:

- homogeneous modeled gross-benefit break-even = **$3,480.41/loan**;
- burnout-aware modeled gross-benefit break-even = **$3,710.04/loan**;
- at **$3,650/loan**, homogeneous MCRIS rejects the intervention with net value **-$16.96M**;
- BAMI accepts it with net value **+$6.00M**.

Evidence-borrowing check:

- current default multiplier = 0.55 on the natural scale;
- after EBC borrowing, posterior multiplier = **0.54059**;
- a compatible historical estimate receives final power **0.61483**;
- a conflicting estimate receives only **0.00983**, showing that conflict is not pooled naively.

TDSX robustness check:

- status = **TIPPING_POINT_FOUND**;
- explored net values span about **-$88.61M to +$49.29M** in the 20,000-loan surface;
- nearest reported grid tipping point is at default multiplier 0.55, cost $4,500/loan, prepayment-cost fraction 0.002.

Interpretation: borrower-selection burnout can be economically decision-relevant rather than a cosmetic forecasting refinement. The effect is parameter-dependent, so BAMI exposes both the homogeneous comparison and an explicit decision surface rather than asserting that burnout always increases value.

Evidence label: **synthetic fixed-parameter benchmark; not real-world mortgage validation**.
