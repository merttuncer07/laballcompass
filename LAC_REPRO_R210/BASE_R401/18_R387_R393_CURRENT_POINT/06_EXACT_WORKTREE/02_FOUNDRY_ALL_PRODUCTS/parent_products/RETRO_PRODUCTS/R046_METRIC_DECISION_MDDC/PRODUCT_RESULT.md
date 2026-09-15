# R-046 product result — MDDC v0.1

**Product route:** standalone metric-versus-decision divergence diagnostic  
**Result:** working product; 4/4 focused tests pass

MDDC converts the historically weakened claim into a falsifiable supplied-candidate search bench.
It does not assume density metrics fail; it reports a ranking inversion only when an explicit belief,
action, and regret witness exists.

The first two-case construction found two action inversions and two metric/decision ranking
inversions. In the strongest witness, the metric-near candidate incurred decision regret 0.06 while
an L1-farther candidate preserved the correct action with zero regret; their L1 distance gap was 0.30.
