# PCBE v0.1 — Preferential-Channel Breakthrough Estimator

PCBE reconstructs wormhole breakthrough on a finite conductance grid. It finds the widest
left-to-right path, measures its bottleneck and tortuosity, solves the full resistor-network pressure
problem, and compares effective system conductance with a baseline field.

A bright or high-conductance feature is not called breakthrough merely because it exists. It must
span to the outlet; when a baseline is supplied, it must also create the declared system-level
conductance jump. This product applies to porous flow, reactive infiltration, fracture, leakage, and
network deployability.

Run `python -m unittest -v test_pcbe.py` and `python demo_breakthrough.py`.
