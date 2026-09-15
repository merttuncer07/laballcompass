# CAPL v0.1 — Constraint-Aware Portfolio Policy Learner

CAPL learns a feature-to-portfolio policy by the realized net return and risk of its actions, not by
first predicting returns and assuming the downstream portfolio will remain feasible. Every proposed
action is projected to a long-only capped simplex and then moved no farther than the declared
turnover limit.

Training uses a derivative-free population search over linear-softmax policies. The returned artifact
contains the policy coefficients, every validation weight, transaction costs, risk-adjusted metrics,
an equal-weight comparison, and counts for sum, bound, and turnover violations. Outperformance is
reported as a measurement rather than made part of the definition of a working policy service.

Run `python -m unittest -v test_capl.py` and `python demo_policy.py`.
