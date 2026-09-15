# R-044 product result — DLEW v0.1

**Product route:** standalone decision-loss training and evaluation workbench  
**Result:** working product; 4/4 focused tests pass

DLEW trains candidate selection on downstream decision regret, evaluates it on untouched outcomes,
and directly tests whether conventional prediction-error ranking would choose a different model.
Every candidate and induced action path remains available even when rankings agree or performance
fails to improve.

Historical decision-focused-learning overlap remains provenance, not a veto.

In the first untouched 1,000-event construction, ordinary RMSE selected `lowest_rmse` (0.006061)
over `decision_boundary` (0.030255). The decision ranking correctly reversed them: common-mode error
left the latter's relative action intact, producing 98.4% oracle-action agreement and mean regret
0.00000968 versus 85.9% and 0.00071308. Decision-based selection reduced validation regret 98.64%
while preserving both full action paths.
