# Product Result — SRCD v0.1

**Retro candidate:** R-043 / S-159 + S-238 + S-930  
**Historical decision:** prior-art collision  
**Product:** Scoring-Rule and Reporting-Contract Designer  
**Status:** independent working product

SRCD maps a desired reported property to a proper score and then verifies whether the implemented
payment transformation still rewards truthful reporting on an empirical outcome distribution.

In the first skewed-outcome construction:

- the elicited mean was **9.9**, median **6.0**, 90% quantile **10.0**, and 90% expectile **25.5**;
- an event frequency of 0.7 was elicited exactly by the Brier contract;
- every raw scoring rule placed its declared target in the optimal set;
- applying a zero payment floor to the mean contract flattened expected payment across reports from
  **2 to 45**, destroying the strict truthful incentive even though the underlying score remained proper.

Four tests pass. SRCD is a standalone forecasting, KPI, and compensation-contract product and does
not require current-product integration.

v0.1 verifies contracts against empirical outcomes. The next standalone layer is distributional log
scores, interval scores, risk aversion, limited liability, multi-agent tournaments, and live backtests.
