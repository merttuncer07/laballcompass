# V2P021_BMDRE — Belief-Metric Decision-Relevant Explorer

Composition: `FOUNDRY:P093 -> PARENT:IM334_IM094_DRE`.

Mechanism: BMDT supplies a path-local distance-to-action-flip. DRE accepts a reduced belief only when its approximation error is strictly smaller than the declared tipping distance; otherwise it requests full belief resolution.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
