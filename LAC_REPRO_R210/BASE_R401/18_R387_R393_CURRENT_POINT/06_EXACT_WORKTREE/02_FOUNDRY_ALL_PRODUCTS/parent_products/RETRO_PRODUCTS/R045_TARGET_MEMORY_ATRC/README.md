# ATRC v0.1 — Adaptive Target-Relevance Retention Controller

ATRC controls a finite example memory for a declared prediction target. On every overflow it measures
the audit loss caused by each possible deletion and removes the least target-useful item, with an
optional explicit age cost. It reports every eviction, retained index, prequential prediction, exact
budget compliance, and FIFO/reservoir comparisons. This narrow executable shell makes no broad
“smart forgetting” novelty claim.

Run `python -m unittest -v test_atrc.py` and `python demo_retention.py`.
