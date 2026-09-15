# SRCD v0.1 — Scoring-Rule and Reporting-Contract Designer

SRCD turns the quantity a decision-maker wants reported into a score and payment contract:

- mean → squared error;
- quantile → pinball loss;
- expectile → asymmetric squared error;
- binary event probability → Brier score.

It verifies the elicited report on the supplied empirical outcome distribution and separately checks
whether payment floors or ceilings create dishonest ties or move the optimum. This distinguishes a
mathematically proper score from an implemented compensation contract that may no longer preserve
the incentive.

SRCD is a standalone forecasting, KPI, and reporting-contract product. It requires no integration
with current products.

Run:

```powershell
python -m unittest -v test_srcd.py
python demo_reporting_contracts.py
```
