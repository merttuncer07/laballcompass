# P095_GSSA — Geometry-Support Shift Audit

**Composition:** WBDP + OWS

Separates geometric Wasserstein shift from importance-weight support fragility.

## Benchmark

W2 is only 0.003146, yet ESS fraction is 0.0925 and OWS reports `SUPPORT_FRAGILE`; max normalized weight is 0.10.

## Claim boundary

Density-ratio audit requires common discrete support and positive source mass in every represented target bin.

## Verification

6/6 product tests passed.
