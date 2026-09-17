# Protocol recorded before execution

Use the unmodified UCI Parkinsons Telemonitoring archive identified by the hashes
in `run.py`. One random subject permutation with seed 20260915: 20 fit subjects,
11 selection subjects, 11 protected subjects. No subject crosses partitions.
Fit the six explicitly defined models once on the 16 voice features; exclude ID,
age, sex, time and both target columns from features. The outcome is the published,
linearly interpolated motor UPDRS score. Use absolute prediction error.

Compare ordinary ACSA row resampling to whole-subject resampling with 2,000 draws
each, the same fitted candidates, loss matrices, seed and pooled-recording
estimand. Report both methods whatever the outcome. No seed search or holdout
tuning. This checks the effect of known source grouping, not prediction quality,
interval coverage, medical usefulness or banking performance. Eleven protected
subjects limit inference. A stronger or weaker interval is an observed result,
not a selection criterion for reporting.

Original records are attributed to Tsanas and Little (2009), UCI, DOI
10.24432/C5ZS3N, CC BY 4.0. `*-losses.csv` will contain derived model errors with
original CSV line numbers and subject IDs, never fabricated source observations.
