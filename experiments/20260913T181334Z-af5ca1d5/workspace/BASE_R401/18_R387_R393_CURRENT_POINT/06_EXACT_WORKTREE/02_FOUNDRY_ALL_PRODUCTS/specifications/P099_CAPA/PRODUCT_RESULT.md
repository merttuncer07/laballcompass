# Product result — P099_CAPA v0.1

**Product:** Constraint-Adaptive Policy Audit  
**Parents:** CAPL + ACSA  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Treats CAPL hyperparameter variants as an adaptive policy family, freezes their learned coefficients, computes per-period protected losses, and audits design-stage hyperparameter selection with ACSA.

## Measured evidence

- **design_selected**: `aggressive`
- **protected_best**: `diversified`
- **selected_protected_regret**: `0.0405579187624988`
- **aggressive_protected_mean_loss**: `0.025686123890703922`
- **diversified_protected_mean_loss**: `-0.014871794871794875`
- **tests**: `6/6`

## Claim boundary

The benchmark is a regime-shift stress test. Per-period loss uses net return plus the declared local risk penalty; it is not a universal portfolio utility.
