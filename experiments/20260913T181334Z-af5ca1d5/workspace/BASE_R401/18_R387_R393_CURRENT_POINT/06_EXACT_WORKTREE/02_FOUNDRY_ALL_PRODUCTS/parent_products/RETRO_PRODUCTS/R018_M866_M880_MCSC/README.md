# MCSC v0.1 — Monotone Comparative-Statics Certifier

MCSC checks every increasing/decreasing-differences rectangle in a finite ordered payoff table. It
returns a structural direction certificate, exact worst violation witness, all argmax sets, and least
and greatest optimal selections. This is a standalone policy, capacity, pricing, and threshold-response
product; integration is unnecessary.

Run `python -m unittest -v test_mcsc.py` and `python demo_comparative_statics.py`.
