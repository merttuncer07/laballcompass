# Hodge Flow Attribution Decomposer

HFAD is an independent retro product from **R-002 / C-326 / M-497–M-498**. The candidate was
historically recorded as `VARIANT_OF IM-320`; it did not receive a new family ID. The preserved
discrete shell nevertheless defines a standalone flow-attribution product.

Given oriented node-edge and edge-face incidence operators plus an observed edge flow, HFAD returns:

- potential/gradient flow carrying source-to-sink imbalance;
- local circulation around filled faces;
- harmonic circulation around global holes;
- component energies and exact reconstruction/orthogonality diagnostics.

A node-balance-only analysis puts both circulation types into one unexplained residual. HFAD tells a
local recirculation problem from a global topological loop, which leads to different interventions.

## Run

```powershell
python -m unittest -v test_hfad.py
python demo_flow_attribution.py
```

## Boundary

v0.1 uses unweighted finite oriented complexes with complete edge observations. Next layers are edge
weights, uncertainty, missing flows, streaming change detection, and automatic face/complex
construction from domain topology.
