# P018 DPCG v0.1 — Decision Privacy Composition Governor

## Composition

DTPR private action/selection releases -> PPSA global privacy accounting.

DTPR already protects one controller's local epsilon budget. DPCG adds a global preflight gate so multiple independent DTPR controllers cannot each stay locally valid while collectively overspending one shared privacy budget. PPSA-valid post-processing remains zero additional privacy cost.

## Claim boundary

DPCG accounts declared DTPR mechanism charges. It does not infer sensitivity, validate the neighboring-dataset definition, or turn a non-DP mechanism into a DP one.
