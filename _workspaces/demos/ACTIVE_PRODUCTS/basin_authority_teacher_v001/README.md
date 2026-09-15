# Basin Authority Teacher v0.0.1

This research product searches for a designed teaching example whose normalized
one-shot gradient update crosses a small neural learner into a better optimizer
basin.  It compares that intervention with the locally loss-greedy example at
the **same update norm**.

The MCES-derived authority firewall requires explicit model-class coverage,
optimizer-scope matching, candidate-map completeness, evidence freshness,
objective and tolerance authority, and observable recovery. Any missing
condition returns `ABSTAIN` before candidate search.

This implementation deliberately makes no global novelty or deployment claim.
Its operating shell is small differentiable learners whose post-intervention
retraining can be evaluated.

v0.0.2 adds a local edge estimator. It bisects a verified bad-to-good parameter
path, ranks candidate teaching gradients by alignment with that estimated edge,
and compares the result with loss-greedy ranking under an equal recorded
post-retraining-unit budget. The original v0.0.1 files and evidence are retained.

Run tests and benchmark:

```powershell
python -m pytest -q lab_products/basin_authority_teacher_v001/test_basin_authority_teacher.py
python lab_products/basin_authority_teacher_v001/run_benchmark.py --output LABALLCOMPASS_INGESTED_BRANCHES_2026-08-27/BASIN_TEACHER_BENCHMARK.json --basins-per-width 2 --candidate-count 36 --retrain-steps 800
python lab_products/basin_authority_teacher_v001/run_edge_benchmark.py --output LABALLCOMPASS_INGESTED_BRANCHES_2026-08-27/BASIN_EDGE_TEACHER_BENCHMARK.json --basins-per-width 2 --candidate-count 36 --retrain-steps 800 --budget 40
```
