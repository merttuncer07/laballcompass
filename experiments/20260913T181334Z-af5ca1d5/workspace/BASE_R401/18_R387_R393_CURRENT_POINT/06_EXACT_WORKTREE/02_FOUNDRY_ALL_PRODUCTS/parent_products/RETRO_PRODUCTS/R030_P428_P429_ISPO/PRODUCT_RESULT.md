# R-030 product result — ISPO v0.1

**Product route:** standalone intermittent search controller  
**Result:** working product; 4/4 tests pass

ISPO evaluates detect-capable local-search blocks alternating with fast detection-blind relocation.
It optimizes against a declared spatial target prior while requiring complete coverage of every
location carrying target probability.

In the first 120-location construction, the prior concentrated on two five-location clusters. Local
search alone required expected detection time 33.0. ISPO selected five local observations followed
by a 55-location relocation, reducing expected time to 6.3125 (80.87%) and worst supported detection
time from 65.0 to 11.625. Candidate orbits that missed possible targets were retained as infeasible,
not rewarded for their artificially short times.

This is a standalone routing/inspection/retrieval product; current-product integration is optional.
