# R-019 product result — VICO v0.1

**Product route:** standalone two-bottleneck operating-point optimizer  
**Result:** working product; 4/4 tests pass

VICO combines measured activation and release rates as serial stages, checks the claimed opposing
directions, and chooses either maximum expected throughput or minimum worst-case regret.

In the first three-scenario construction, the individual best couplings were 4, 5, and 6. VICO chose
coupling 5, achieved weighted throughput 3.21284, and limited maximum scenario regret to 0.07143.
When the tested grid ended at coupling 3 while throughput was still rising, it returned
`SEARCH_RANGE_MISSES_INTERIOR_OPTIMUM` instead of treating the boundary as a Sabatier optimum.

The historical mechanism therefore supports a standalone process-tuning product. It does not need
to attach to an existing LABALLCOMPASS product.
