# Product result — P123_SCGD v0.1

**Product:** Support-Covariance Guard Designer  
**Parents:** SACPS + CSID  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Deletes each declared covariance-support edge, re-solves the minimum-variance portfolio, measures protected holdout-risk damage, and safeguards the most consequential support relation.

## Measured evidence

- **baseline_realized_variance**: `0.31936934674716017`
- **consequence_by_edge**: `{'0-1': 39.854394230042054, '0-2': 1.3077867156962575, '0-3': 2.139308810502838, '1-2': 0.0, '1-3': 1.49941693858896, '2-3': 13.899152027742556}`
- **selected_safeguards**: `('protect_0-1',)`
- **status**: `COVARIANCE_SUPPORT_FAILURES_ROUTED_TO_GUARDS`
- **tests**: `6/6`

## Claim boundary

The holdout covariance is treated as protected evaluation evidence; support-edge failure probabilities remain declared inputs.
