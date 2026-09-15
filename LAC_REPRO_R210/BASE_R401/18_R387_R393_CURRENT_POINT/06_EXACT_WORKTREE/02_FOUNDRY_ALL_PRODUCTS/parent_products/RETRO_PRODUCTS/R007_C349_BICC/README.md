# BICC v0.1 — Bounded-Influence Concentration Certificate

BICC audits how replacing one input at a time changes a scalar black-box output. It reports:

- per-coordinate RMS, mean absolute, and maximum observed replacement effects;
- an Efron–Stein variance upper proxy from independent coordinate replacements;
- a McDiarmid two-sided radius when global coordinate sensitivity bounds are supplied;
- dominant-bound share and effective coordinate count;
- explicit status when supplied bounds are contradicted by observed replacements.

The tool never promotes sampled maxima into global mathematical bounds. Without supplied bounds its
status is `EMPIRICAL_INFLUENCE_ONLY`; with bounds it returns an assumption-conditional certificate.

Run:

```powershell
python -m unittest -v test_bicc.py
python demo_influence_audit.py
```

BICC is a standalone reliability product. It does not require integration with the completed current
composition products.
