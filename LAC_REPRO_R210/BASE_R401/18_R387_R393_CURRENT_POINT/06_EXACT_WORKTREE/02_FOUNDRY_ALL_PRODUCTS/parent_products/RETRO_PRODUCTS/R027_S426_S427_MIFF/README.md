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

## 2026-09-15 minimum-cut repair

MIFF now optimizes declared integer/binary-float cut costs with exact integer residuals. Small costs no longer disappear under a fixed epsilon, and large costs cannot make a super-terminal edge look cheaper than the real cut. Parallel/reverse flows and multiple terminals remain supported; unrepresentable floating-point totals raise an explicit error. DREW's embedded MIFF copy is identical to the canonical parent.

Fresh scope: 24 MIFF tests and 11 DREW tests pass. Includes an exhaustive vertex-partition oracle on small graphs and NetworkX's independently specified directed-graph cut of 23. This is a known graph algorithm repair. Gains, suspect labels and costs remain declared model inputs; no calibrated probability, real pipeline enforcement or audit-field benefit is established. Full observations, preserved originals and proof are in `restoration/20260915-miff` at the repository root.
