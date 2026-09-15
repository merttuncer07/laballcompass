# R-047 product result — MCRIS v0.1

**Product route:** standalone mortgage transition/intervention simulator  
**Result:** working product; 4/4 tests pass

MCRIS evolves performing, delinquent, defaulted, and prepaid balances jointly, preserving cohort
mass while default and prepayment compete for surviving loans. Intervention value includes credit
loss, prepayment opportunity cost, and implementation cost.

In the first 10,000-loan, 60-month construction, the intervention avoided 761.09 defaults but also
created 458.76 incremental prepayments. It reduced modeled economic loss by 60.99 million; after a
6.5 million intervention cost, net value remained 54.49 million.

Positive-control provenance confirms a known transfer; it does not prevent operational use.
