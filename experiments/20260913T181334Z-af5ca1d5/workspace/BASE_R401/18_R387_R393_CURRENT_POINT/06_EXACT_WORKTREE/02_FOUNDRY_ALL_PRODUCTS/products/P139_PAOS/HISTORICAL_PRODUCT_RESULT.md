# P139 PAOS — Protected Averaging-Operator Selection

Parents: OASRD -> ACSA.

OASRD alpha values are kept as a candidate family instead of selecting one permanently from the same operator regime. Their fixed-point residuals are measured across selection and untouched operator families and audited by ACSA.

Benchmark: selection chooses direct iteration `alpha=1` with mean residual 6.62e-7 versus 0.00374 for alpha=0.5. On the protected family, alpha=1 residual explodes to 130.54 while alpha=0.5 is 1.33e-7. Protected regret is 130.54.

Claim boundary: the protected operator family must represent a real deployment distribution; the audit does not infer it automatically.

Status: WORKING_COMPOSITION; 6/6 tests.
