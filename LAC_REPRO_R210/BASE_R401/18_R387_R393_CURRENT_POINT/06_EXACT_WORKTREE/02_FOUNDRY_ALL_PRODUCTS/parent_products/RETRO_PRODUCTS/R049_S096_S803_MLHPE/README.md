# MLHPE v0.1 — Multi-List Hidden Population Estimator

MLHPE provides a bias-corrected Chapman estimate for two lists and a three-list Poisson log-linear
model surface for the unobserved `000` capture cell. It fits independence and every subset of pairwise
list interactions, reporting:

- unseen and total population estimates with intercept-based uncertainty;
- AIC/BIC, Akaike weights, residual diagnostics, and interaction multipliers;
- best-model and model-averaged totals;
- the full total-estimate range and dependence-sensitivity level;
- an explicit warning when the observed seven-cell table is saturated. Saturated models remain in
  the sensitivity surface but are excluded from automatic best-model selection and model averaging.

MLHPE is a standalone hidden-population and coverage-gap product. No current-product integration is
required.

Run:

```powershell
python -m unittest -v test_mlhpe.py
python demo_hidden_population.py
```
