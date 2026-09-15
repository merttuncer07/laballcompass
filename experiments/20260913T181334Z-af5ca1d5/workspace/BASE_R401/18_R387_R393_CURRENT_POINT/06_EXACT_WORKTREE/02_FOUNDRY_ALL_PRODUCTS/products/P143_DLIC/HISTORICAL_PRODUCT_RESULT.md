# P143 DLIC — Discrete Liquidity Integrality Certificate

Parents: LCM -> RIC.

DLIC reconstructs the actual eligible claim-channel allocation constraint matrix used by LCM and asks RIC whether the continuous allocation has a theorem-backed integer-unit interpretation.

Benchmark: with unit advance rates and integer claim/capacity/anchor RHS, the 8x4 matrix is totally unimodular (maximum absolute subdeterminant 1) and discrete liquidity units are certified. With advance rate 0.8 the matrix is non-integral and the certificate is explicitly dropped, although LCM still solves a valid continuous allocation with deployable liquidity 8.

Claim boundary: TU certification does not apply through fractional conversion coefficients or fractional RHS merely because the LP solution happens to look integral.

Status: WORKING_COMPOSITION; 6/6 tests.
