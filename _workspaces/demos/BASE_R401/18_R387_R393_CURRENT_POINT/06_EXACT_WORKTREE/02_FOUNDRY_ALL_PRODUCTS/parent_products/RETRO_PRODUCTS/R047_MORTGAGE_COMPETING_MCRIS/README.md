# MCRIS v0.1 — Mortgage Competing-Risk Intervention Simulator

MCRIS evolves performing, delinquent, defaulted, and prepaid mortgage states month by month. Default
and prepayment compete for the same surviving loans, so an intervention cannot claim every avoided
default without accounting for the prepayments that removed those loans from later risk.

The product measures state paths, credit loss, prepayment opportunity cost, intervention cost,
defaults avoided, and net value. A known transfer from competing-risk methodology is still a useful
operational product; positive-control status is not a reason to discard it.

Run `python -m unittest -v test_mcris.py` and `python demo_mortgage.py`.
