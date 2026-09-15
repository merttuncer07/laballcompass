# MBPF v0.1 — Mortgage Burnout-adjusted Prepayment Forecaster

MBPF represents a mortgage pool as latent prepayment-propensity classes. Every month, high-propensity
borrowers leave faster, automatically lowering the average propensity of the surviving pool. The
forecast reports class survival, effective monthly prepayment, competing defaults, and the error from
holding the original average propensity fixed.

The mechanism is useful beyond novelty claims: it prevents servicing, duration, and liquidity plans
from assuming that the borrowers remaining after a refinancing wave resemble the original pool.

Run `python -m unittest -v test_mbpf.py` and `python demo_burnout.py`.
