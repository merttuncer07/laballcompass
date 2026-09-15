# P042 HPMD v0.1 — Hidden-Population Model Decision Audit

## Capability

HPMD composes MLHPE's capture-dependence model surface with MDDC's metric-versus-decision audit. Non-saturated capture models become hidden decision states; normalized Akaike weights form a declared reference model belief; capacity actions are scored by explicit shortage and excess costs.

## Benchmark result

For the high-dependence three-list example, MLHPE's best AIC model (`AB`) estimates total population at roughly **1031**, while the model-weighted total is about **1085** and substantial weight remains on models around 1113–1129. With capacities `{950,1050,1150,1250}` and shortage cost twice excess cost:

- best-AIC point selection chooses **1050**;
- the full model-belief decision chooses **1150**;
- MDDC reports an action inversion and material regret above **20 loss units** for collapsing to the best model.

Under symmetric shortage/excess cost, both select 1050, proving the product is decision-targeted rather than merely preferring model averaging.

## Claim boundary

Akaike weights are used as a declared decision-weighting convention; HPMD does not claim they are literal Bayesian posterior probabilities. Saturated zero-residual-DF models remain excluded as in MLHPE. Capacity loss parameters are operator inputs.

## Verification

6/6 product tests pass.
