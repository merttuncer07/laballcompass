# V2P009 SGMB — development adapter result

**Composition:** Foundry `P140 BOSA` + LCB `MultiFidelityBudgetControllerV0`

**Name:** Support-Gated Multi-Fidelity Budgeting

## Neutral primitive

`selection changes target population -> audit effective support -> if support usable, optimize fine/cheap counts by cross-fidelity correlation -> if support fragile, disable cheap channel and route budget fine-only`

## Honest interface

K048 assumes its pilot cross-fidelity relationship is informative for the population where the measurement program will run. P140 BOSA identifies a specific way this can fail: survivor selection changes the late population until the initial cohort has weak effective support. SGMB therefore makes BOSA support a necessary gate before a cheap proxy can enter K048's budget allocation.

This is non-additive: a correlation-only controller can allocate heavily to the cheap channel at month 24 even when BOSA reports fragile support. SGMB converts that support failure into a changed feasible set (`n_cheap = 0`) rather than merely attaching a warning.

## Contrastive boundary benchmark

In the preserved BOSA burnout shell, month-24 ESS fraction is below the declared 0.80 floor. With pilot correlation 0.95, a mechanism-removing K048 comparator still selects a multi-fidelity program with cheap acquisitions. SGMB routes the same budget fine-only, reducing unsupported cheap acquisitions to zero. Early supported months preserve the K048 allocation exactly.

The benchmark proves routing semantics in this declared synthetic mortgage-survivor shell. It does not show that every cheap measurement becomes biased when ESS is low, nor that fine-only is universally optimal.

## Working region

- BOSA's cohort/survivor model is the relevant support shell.
- The ESS floor is declared before routing.
- Fine and cheap costs plus pilot correlation are declared.
- Fine-only fallback is feasible.

## Failure / abstention region

- BOSA is a support audit, not a causal estimator.
- Support usability does not itself prove proxy calibration.
- Fragile support does not identify the direction or magnitude of proxy bias.
- Domain-native held-out evidence is required before operational deployment.

## Development checks

- 12/12 focused tests pass.
- Supported branch preserves corrected K048 counts.
- Fragile support overrides even near-perfect pilot correlation.
- Mechanism-removing comparator is K048 without support gating.

**Evidence:** executable deterministic-shell routing result; no external transfer claim.
