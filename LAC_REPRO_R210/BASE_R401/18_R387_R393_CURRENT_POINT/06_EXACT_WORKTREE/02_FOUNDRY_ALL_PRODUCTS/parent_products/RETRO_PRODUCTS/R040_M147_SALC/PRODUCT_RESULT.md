# Product Result — SALC v0.1

**Retro candidate:** R-040 / M-147  
**Historical decision:** prior-art collision  
**Product:** State Aggregation and Lumpability Certificate  
**Status:** independent working product

SALC checks whether a proposed state partition preserves the Markov property and produces either an
exact aggregate transition matrix or a quantified approximate model.

In the first four-to-two-state construction:

- exact block transition signatures produced matrix `[[0.8,0.2],[0.2,0.8]]`;
- 30-step maximum aggregate-distribution error was **9.16e-16**;
- a controlled violation changed one block-transition total by **0.05**;
- the approximate aggregate retained maximum one- and 30-step TV error **0.025**;
- the exact offending source block, target block, and micro-state pair were reported.

Four tests pass. SALC is a standalone regime, reliability, customer-state, and credit-state model
compression product; current-product integration is not required.

v0.1 accepts user-proposed finite partitions. The next standalone layer is automatic partition search,
reward-aware aggregation, uncertainty intervals, and continuous-time chains.
