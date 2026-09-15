# MIFF v0.1 — Modular Inference Flow Firewall

MIFF treats an inference or decision pipeline as modules joined by directed information flows. The
operator declares suspect modules, protected modules, feedback gains, and the operational cost of
cutting each flow. MIFF then:

- enumerates suspect-to-protected paths;
- finds the minimum-cost set of information flows that blocks every such path;
- measures closed-loop contamination before and after the cut; and
- detects when the cut changes an unstable feedback loop into a stable modular pipeline.

The suspect module is not deleted. Its diagnostics and safe outputs can continue operating; only the
declared contaminating feedback path is blocked.

Run `python -m unittest -v test_miff.py` and `python demo_firewall.py`.
