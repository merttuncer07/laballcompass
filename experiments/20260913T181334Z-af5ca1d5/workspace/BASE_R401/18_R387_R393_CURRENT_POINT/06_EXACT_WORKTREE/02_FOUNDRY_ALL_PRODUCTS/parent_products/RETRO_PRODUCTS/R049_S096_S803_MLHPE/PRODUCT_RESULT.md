# Product Result — MLHPE v0.1

**Retro candidate:** R-049 / S-096 + S-803 + S-812  
**Historical decision:** positive-control / broadly transferred  
**Product:** Multi-List Hidden Population Estimator  
**Status:** independent working product

MLHPE estimates the never-observed population using a Chapman two-list estimator and a complete
three-list surface of independence and pairwise-interaction Poisson log-linear models.

In the first 580-observation three-list construction:

- model totals ranged from **713.3 to 1,494.3**, a **2.095×** dependence-sensitive span;
- dependence sensitivity was classified **HIGH**;
- the best selectable model used AB dependence and estimated **1,030.9** total people;
- selectable-model averaging estimated **1,084.9**;
- the saturated observed-table model remained visible at 1,494.3 but received zero selection weight
  because it had no residual degree of freedom;
- a two-list reference estimated 499.7 total and 114.7 unseen.

Four tests pass. MLHPE is a standalone hidden-population and coverage-gap product; integration with
the current products is not required.

v0.1 handles two or three linked lists with exact capture histories. The next standalone layer is
linkage uncertainty, more lists with sparse-model regularization, covariates, and bootstrap intervals.
