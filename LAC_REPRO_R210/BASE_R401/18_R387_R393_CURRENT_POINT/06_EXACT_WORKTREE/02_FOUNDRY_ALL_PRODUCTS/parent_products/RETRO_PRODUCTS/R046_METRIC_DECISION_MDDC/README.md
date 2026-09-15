# MDDC v0.1 — Metric–Decision Divergence and Counterexample Bench

MDDC scores belief approximations by L1/KL reconstruction error and by the regret of the action they
induce. It then returns exact witnesses where the metric-preferred approximation makes the worse
decision. Supplied candidates are never discarded, and absence of a witness is reported honestly.

Run `python -m unittest -v test_mddc.py` and `python demo_divergence.py`.
