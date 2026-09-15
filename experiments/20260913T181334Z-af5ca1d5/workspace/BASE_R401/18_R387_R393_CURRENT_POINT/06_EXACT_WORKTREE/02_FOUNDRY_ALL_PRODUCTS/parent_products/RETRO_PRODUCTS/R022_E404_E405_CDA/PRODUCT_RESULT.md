# Product Result — CDA v0.1

**Retro candidate:** R-022 / E-404–E-405  
**Historical decision:** merged into IM-034  
**Product:** Channel Dominance Auditor  
**Status:** independent working product

CDA turns a merged theorem shell into a channel-audit product. It determines whether one finite
information channel can be produced from another by data-independent stochastic garbling and keeps
incomparability when channels reveal different state partitions.

In the reproducible three-state construction:

- the imposed garbling matrix was recovered with maximum error **1.11e-16**;
- the reverse direction's best achievable error was **0.4097**, certifying strict one-way dominance;
- detailed-channel decision value was **0.4150**;
- coarse-channel decision value was **0.0725**;
- garbling destroyed **0.3425** of decision value for the declared action problem.

Four tests pass: known garbling, signal-relabeling equivalence, incomparable partitions, and the
decision-value monotonicity implied by dominance. CDA is independent of the prior product set.

v0.1 uses known finite channels. The next standalone layer is sampling uncertainty, confidence
regions, continuous signals, and robust value across classes of priors/utilities.

