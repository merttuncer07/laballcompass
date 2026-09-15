# VICO v0.1 — Volcano Interior-Coupling Optimizer

VICO turns the Sabatier/volcano mechanism into a standalone operating-point product. Given measured
or simulated activation and release rates across an ordered coupling grid, it:

- verifies that activation improves while release worsens;
- combines the two serial bottlenecks into achievable throughput;
- selects expected-throughput or minimax-regret coupling across scenarios;
- distinguishes a real interior optimum from an insufficient search range; and
- returns an exact witness when the opposing-bottleneck assumption fails.

It does not ask whether the volcano relation is academically novel. It asks where to operate a real
two-stage process and whether the available data support that decision.

Run `python -m unittest -v test_vico.py` and `python demo_coupling.py`.
