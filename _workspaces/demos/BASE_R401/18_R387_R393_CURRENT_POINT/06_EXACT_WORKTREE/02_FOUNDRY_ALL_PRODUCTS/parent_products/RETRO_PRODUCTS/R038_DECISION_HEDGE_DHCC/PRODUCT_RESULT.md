# R-038 product result — DHCC v0.1

**Product route:** standalone decision-focused hedge calibrator  
**Result:** working product; 4/4 tests pass

DHCC constructs every declared covariance-ridge hedge and selects by untouched residual variance
plus any explicit turnover cost. It reports the action, conditioning, and realized risk rather than
ranking covariance matrices in isolation.

In the first collinear three-hedge construction, DHCC selected ridge 0.003. Validation variance fell
from 1.26685 unhedged and 0.16672 with the unregularized hedge to 0.15723—a reduction of 87.59% and
an additional 5.69%, respectively. The chosen hedge's condition number was 607.89 versus 2633.23
unregularized.

Prior-art overlap is retained as provenance and does not prevent standalone product use.
