# Product result — P002 DCPS v0.1

**Route:** B — observable state to constrained action  
**Parents:** PSCT + DSBC + CAPL + DLEW  
**Promotion state:** `WORKING_COMPOSITION`  
**Result:** new standalone state-reduction / policy-feature product

## New capability

Neither PSCT nor DSBC alone certifies the conjunction needed by a recursively used decision state.
PSCT protects predictive closure but not decision irrelevance; DSBC protects bounded decision regret
but explicitly does not claim Markov/predictive closure. DCPS composes the two certificates and adds
partition refinement so a state merge survives only when both properties hold on the observed shell.

This directly operationalizes the distinction:

`same action now` **does not imply** `same state for future decisions`.

## Measured results

- 7/7 DCPS tests pass.
- Compatible process: `4 PSCT states → 2 DSBC clusters → 2 decision-closed clusters`.
- Dynamically incompatible process: `4 → 2` by DSBC alone, then closure refinement returns `4`; the
  unsafe compression is not accepted.
- CAPL adapter: zero sum/bound/turnover violations on validation.
- Synthetic policy benchmark: two-state DCPS uses 3 coefficient rows versus 5 for raw four-state
  context representation and improves the declared validation objective in the fixed construction.
- DLEW representation comparison: prediction-RMSE selects `predictive_state`, decision-loss selects
  `decision_closed`; final decision regret is equal between the 4-state and 2-state representations.
- Unseen validation contexts are an explicit interface error for CAPL when complete coverage is
  required; there is no silent nearest-state assignment.

## Known boundary

DCPS closure is empirical on the PSCT observed context shell. It is not a theorem about unseen
histories. A real-data pilot should therefore report context coverage and unresolved rates alongside
policy performance.
