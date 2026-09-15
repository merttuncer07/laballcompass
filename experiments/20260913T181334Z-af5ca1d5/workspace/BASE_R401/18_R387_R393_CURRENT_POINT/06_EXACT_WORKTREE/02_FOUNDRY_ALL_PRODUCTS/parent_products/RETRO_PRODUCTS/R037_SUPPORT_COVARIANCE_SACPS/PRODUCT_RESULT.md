# R-037 product result — SACPS v0.1

**Product route:** standalone covariance/precision decision service  
**Result:** working product; 4/4 tests pass

SACPS enforces a declared covariance support, searches diagonal shrinkage, and validates the full
matrix on untouched observations. It then constructs a minimum-variance action so numerical quality
is tested against a real downstream decision.

In the first 12-variable construction, holdout scoring selected shrinkage 0.15. The condition number
fell from 99.62 for the raw sample covariance to 30.67, every unsupported covariance remained exactly
zero, and realized portfolio variance fell from 0.06249 to 0.04295—a 31.27% reduction.

The historical prior-art collision is retained as provenance, not used as a product veto.
