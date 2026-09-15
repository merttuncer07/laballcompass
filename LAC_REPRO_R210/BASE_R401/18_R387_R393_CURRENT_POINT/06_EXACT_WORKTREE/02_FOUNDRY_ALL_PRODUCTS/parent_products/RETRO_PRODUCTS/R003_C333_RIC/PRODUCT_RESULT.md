# Product Result — RIC v0.1

**Retro candidate:** R-003 / C-333 / M-532–M-536  
**Historical decision:** `VARIANT_OF IM-321`  
**Product:** Relaxation Integrality Certifier  
**Status:** independent working product

RIC converts the preserved integral-geometry shell into an optimization audit. It distinguishes an
LP whose structure certifies integer vertices from one that merely happens to return a convenient
solution for a chosen objective.

In the reproducible constructions:

- the 3×3 assignment constraint matrix was certified totally unimodular, with maximum absolute
  subdeterminant **1**;
- LP and integer assignment solutions were identical with objective **5.0** and gap **0**;
- the triangle vertex-cover matrix returned an explicit 3×3 violating minor of determinant
  magnitude **2**;
- its LP optimum was the fractional vector `(0.5, 0.5, 0.5)` with objective **1.5**, while the
  integer optimum was **2.0**, exposing gap **0.5**.

Four automated tests pass. RIC is standalone and does not depend on the completed product set.

v0.1 exhaustively checks small matrices. The next independent layer is sparse/network subclass
recognition, larger certificates, decomposition, and solver-model import.

