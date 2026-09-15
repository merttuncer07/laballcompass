# Product Result — AICC v0.1

**Composition:** IM-359 → IM-014  
**Product:** Adaptive Information-Channel Controller  
**Status:** working reference product

AICC treats the offered information channel as a sequential control. For every channel it integrates
over possible observations, computes the posterior actions those observations would induce, and
subtracts measurement cost. The selected channel therefore follows the current uncertainty and
decision boundary; measurement stops when no channel has positive remaining decision value.

In 3,000 reproducible episodes per policy with five available measurement opportunities:

- repeated use of a fixed demand channel produced mean decision-regret-plus-cost **0.09245**;
- round-robin demand/failure measurement produced **0.01315**;
- AICC produced **0.006883**, reductions of **92.55%** and **47.67%**, respectively;
- fixed and round-robin policies each used 15,000 measurements, while AICC stopped after **6,838**;
- AICC used the deliberately precise, high-variance nuisance channel **zero times**, because it could
  not change any downstream action.

Three unit tests pass. v0.1 uses a shared sender/receiver objective and Gaussian linear offered
channels. The live extension path is strategic objective mismatch, endogenous signal/garbling
design, non-Gaussian beliefs, repeated-agent response, and disclosure constraints.
