# Product Result — DRE v0.1

**Composition:** IM-334 → IM-094  
**Product:** Decision-Relevant Explorer  
**Status:** working reference product

DRE converts the claim that an action can produce both reward and information into an executable
finite-horizon policy. It explores an uncertain action only to the extent that an observation can
move that action across the current decision boundary and improve later choices. Raw uncertainty is
not itself treated as value.

In the reproducible 2,000-episode, 80-decision construction:

- uncertainty-only exploration incurred mean pseudo-regret **154.6000** and spent **38** pulls per
  episode on a high-variance but decision-irrelevant action;
- a greedy posterior-mean policy incurred mean pseudo-regret **3.0309**;
- DRE incurred mean pseudo-regret **1.7055**, a **98.90%** reduction relative to uncertainty-only
  exploration and a **43.73%** reduction relative to greedy;
- DRE spent **zero** pulls on the deliberately irrelevant high-variance action;
- its final best-action identification accuracy was **54.55%**, versus **26.60%** for greedy in this
  deliberately close-action construction.

Three unit tests pass. They establish that posterior variance contracts, a near decision contender
receives positive information value, and a far-below high-variance action is not selected merely for
being uncertain.

This is a first operational shell, not a claim that the idea is finished. The live extension path is
correlated/contextual actions, non-Gaussian outcomes, action-dependent information channels, and
policies that distinguish the value of learning for control from terminal best-action identification.
