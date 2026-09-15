# ISPO v0.1 — Intermittent Search Policy Optimizer

ISPO converts facilitated diffusion and intermittent search into an executable routing product for
inspection, maintenance, retrieval, patrol, and sparse-target discovery. It evaluates periodic
policies that alternate slow detection-capable local search with fast detection-blind relocation.

The optimizer uses a declared target-location prior, requires complete coverage of its support, and
compares every candidate with a local-only baseline. Policies whose orbit misses possible targets
remain visible as infeasible; speed does not excuse blindness.

Run `python -m unittest -v test_ispo.py` and `python demo_search.py`.
