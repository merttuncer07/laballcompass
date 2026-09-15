# P037 MCST v0.1 — Monotone-Certificate Sensitivity Tipping

## Capability

MCST turns MCSC's pointwise monotone-comparative-statics certificate into a TDSX assumption surface. At every declared assumption point, MCSC remains the exact structural oracle; TDSX searches for the nearest point where the direction-specific violation exceeds tolerance.

## Benchmark result

For actions and parameters `{0,1,2}`, nominal interaction `-1.8` satisfies increasing differences. The declared grid spans `-2.4` to `-1.6`. The nearest certificate-breaking point is **-2.05**; MCST returns both the TDSX tipping distance and MCSC's exact violating rectangle witness there. At `-2.0` the cross-difference is exactly zero and still satisfies the weak certificate.

## Claim boundary

Robustness is conditional on the supplied payoff builder and finite assumption grid. MCST does not extrapolate a global theorem beyond that surface. The scalar passed to TDSX is MCSC's exact violation magnitude, not a surrogate monotonicity score.

## Verification

6/6 product tests pass.
