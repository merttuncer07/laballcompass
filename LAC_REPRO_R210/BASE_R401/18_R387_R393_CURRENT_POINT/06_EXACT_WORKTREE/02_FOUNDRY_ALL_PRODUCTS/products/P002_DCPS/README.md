# DCPS v0.1 — Decision-Closed Predictive State

DCPS composes PSCT and DSBC into a stronger state-reduction certificate, then exposes the resulting
representation to CAPL and DLEW.

PSCT defines state by observable future consequences and tests recursive update closure. DSBC can
then compress those predictive-state probability vectors according to downstream decision regret.
The missing step is crucial: a DSBC merge can be perfectly safe for the current action yet destroy
the ability of the compressed state to update consistently after the next observation.

DCPS therefore performs:

`observable sequence → PSCT predictive states → DSBC decision compression → transition-signature refinement → decision-closed state representation`.

The refinement is split-only. It never weakens DSBC's regret certificate: if a decision-safe merge
breaks closure, that cluster is divided until every observed `(compressed state, next symbol)` has at
most one compressed target state. If PSCT itself is not closed, DCPS preserves that failure instead
of pretending the downstream partition repaired it.

## Downstream adapters

- `transform_sequence(...)` converts causal histories into one-hot DCPS features.
- `learn_constrained_policy_from_representation(...)` feeds those features to CAPL without imputing
  unseen contexts silently.
- `evaluate_representation_predictors(...)` fits memoryless, raw-context, predictive-state, and
  decision-closed mean-return predictors and compares them using DLEW.

CAPL → DLEW is not forced directly: CAPL outputs a continuous constrained portfolio path while DLEW
expects predictive outputs plus a finite action set. DCPS uses CAPL's native policy metrics and uses
DLEW to compare representation-induced predictors instead.

## Evidence

New tests: **7/7 passing**.

Safe order-2 process: PSCT found 4 predictive states; DSBC compressed them to 2 decision-equivalent
states; closure refinement required 0 splits, so the 2-state representation was certified.

Adverse order-2 process: PSCT again found 4 states; DSBC compressed to 2 based on current action, but
those merges had incompatible future transition signatures. DCPS performed 2 refinement splits and
returned 4 states, preventing an invalid 50% compression.

In the policy benchmark, the certified 2-state representation used 3 coefficient rows versus 5 for
the 4-state raw-context policy, with zero portfolio-constraint violations. Its validation objective
was `-0.00887149` versus `-0.00853617` for raw context and `-0.00446051` for a memoryless policy in
that construction. The optimization benchmark is synthetic; the important invariant is preserved
closure + bounded decision regret + zero action-constraint violations, not that one seed happened to
win on objective.

DLEW selected the 4-state predictive representation by prediction RMSE but the 2-state DCPS
representation by decision loss; on final validation they had identical mean decision regret
`0.00124989` and identical oracle-action agreement `0.91569`, while DCPS retained only two states.

Run:

```bash
python -m unittest -v test_dcps.py
python benchmark_route_b.py
```
