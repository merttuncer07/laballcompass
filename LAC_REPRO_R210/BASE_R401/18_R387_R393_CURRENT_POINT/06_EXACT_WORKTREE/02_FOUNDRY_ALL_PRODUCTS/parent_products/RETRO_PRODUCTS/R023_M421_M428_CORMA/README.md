# CORMA v0.1 — Controllability, Observability, and Realization Minimality Auditor

CORMA audits a discrete-time linear state-space model using finite-horizon controllability and
observability matrices and Gramians. It reports:

- controllability and observability ranks and weak directions;
- the four Kalman behavioral category counts;
- input–output Hankel rank as the minimal realization dimension;
- redundant state count, stability, spectral radius, and Gramian spectra.

It diagnoses whether internal states can be actuated, observed, or removed without changing external
input–output dynamics. CORMA is a standalone system-model architecture product and needs no current
product integration.

Run:

```powershell
python -m unittest -v test_corma.py
python demo_state_audit.py
```
