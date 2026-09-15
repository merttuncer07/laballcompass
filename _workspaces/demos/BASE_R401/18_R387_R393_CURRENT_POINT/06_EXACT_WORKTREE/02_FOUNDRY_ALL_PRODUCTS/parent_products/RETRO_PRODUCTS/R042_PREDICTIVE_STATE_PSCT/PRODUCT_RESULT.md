# R-042 product result — PSCT v0.1

**Product route:** standalone predictive-state discovery and closure tester  
**Result:** working product; 4/4 focused tests pass

PSCT constructs state from future-observation laws and refuses to equate one-step predictive
similarity with a recursively valid state. Every compression includes a separate update-closure
audit and keeps the violating transitions visible.

Historical computational-mechanics and predictive-state overlap remains provenance, not a product
veto.

In the first four-symbol construction, PSCT found two predictive states (50% compression), improved
average log loss by 0.25996 versus a memoryless distribution, and certified zero observed closure
violations. A deliberately misleading second-order construction also compressed four contexts to two
for one-step prediction, but PSCT measured a 49.20% update-closure violation rate and returned
`PREDICTIVE_PARTITION_FAILS_CLOSURE`.
