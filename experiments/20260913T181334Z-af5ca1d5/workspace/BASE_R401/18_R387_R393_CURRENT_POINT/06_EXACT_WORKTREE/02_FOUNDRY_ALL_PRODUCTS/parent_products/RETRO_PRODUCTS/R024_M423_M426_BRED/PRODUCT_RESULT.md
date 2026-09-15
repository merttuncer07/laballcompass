# Product Result — BRED v0.1

**Retro candidate:** R-024 / M-423 + M-424 + M-425 + M-426  
**Historical decision:** merged into IM-178 / IM-124  
**Product:** Balanced Reduction Error-budget Designer  
**Status:** independent working product

BRED balances a stable discrete-time linear model and returns the smallest reduced A/B/C/D system
whose discarded Hankel singular values satisfy a user-selected error budget.

In the first six-state construction:

- an error budget of **0.02** selected order **2**;
- the retained Hankel share was **99.895%**;
- the theoretical error upper bound was **0.01582**;
- the measured 300-step maximum impulse error was **0.00306**, with L2 error **0.00672**;
- the reduced spectral radius was **0.919**, preserving stability.

Four tests pass, including budgeted removal, exact zero-budget retention, reduced stability, and
rejection of unstable inputs. BRED is a standalone model-compression/deployment product; current
product integration is not required.

v0.1 targets strictly stable discrete-time LTI models. The next standalone layer is frequency-weighted
reduction, parametric uncertainty, continuous time, and empirical model compression.
