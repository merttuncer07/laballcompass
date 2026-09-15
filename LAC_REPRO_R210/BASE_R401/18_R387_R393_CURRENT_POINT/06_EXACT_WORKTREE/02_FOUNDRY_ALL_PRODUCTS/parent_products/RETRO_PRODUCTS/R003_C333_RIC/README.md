# Relaxation Integrality Certifier

RIC is an independent retro product from **R-003 / C-333 / M-532–M-536**. C-333 was historically
recorded as `VARIANT_OF IM-321`; the exact assignment/network/integral-polyhedron shell is still a
standalone optimization audit.

RIC can:

- exhaustively certify total unimodularity for small integer matrices;
- return the exact first subdeterminant that violates the certificate;
- state when integer right-hand sides license the LP-integrality theorem;
- solve the LP relaxation and integer model side by side;
- report fractional solutions and the realized integrality gap.

## Run

```powershell
python -m unittest -v test_ric.py
python demo_integrality_audit.py
```

## Boundary

Exhaustive minor enumeration is intentionally limited to small matrices. Larger production models
need polynomial recognizers for network/TU subclasses, decomposition, sparse certificates, and
solver-model import rather than brute-force determinant enumeration.
