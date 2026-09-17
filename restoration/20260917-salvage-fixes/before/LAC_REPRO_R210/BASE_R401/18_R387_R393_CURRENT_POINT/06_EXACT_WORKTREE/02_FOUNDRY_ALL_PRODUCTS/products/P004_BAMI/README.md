# P004 — BAMI v0.1

Burnout-Aware Mortgage Intervention workbench.

Directed composition:

1. MBPF supplies the monthly selection-adjusted performing-prepayment hazard path.
2. MCRIS supplies the competing-risk intervention and economic-loss accounting structure.
3. EBC borrows historical intervention-effect evidence on the log default-multiplier scale, with conflict downweighting.
4. TDSX searches the intervention decision surface for net-value tipping points.

BAMI does not assume that surviving borrowers keep the original prepayment propensity mix. It explicitly compares the resulting burnout-aware intervention value with the homogeneous-parent approximation.

Evidence status: executable product with unit tests and a fixed-parameter synthetic decision benchmark. It is not a calibrated mortgage production model and is not real-world validation.
