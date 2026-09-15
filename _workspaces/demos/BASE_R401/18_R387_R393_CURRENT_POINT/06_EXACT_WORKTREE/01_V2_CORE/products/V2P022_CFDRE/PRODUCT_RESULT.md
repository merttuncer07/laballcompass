# V2P022_CFDRE — Closure-Fidelity Decision-Relevant Explorer

Composition: `FOUNDRY:P141 -> PARENT:IM334_IM094_DRE`.

Mechanism: PCFT predictive-closure fidelity is used as a representation gate for DRE. Reduced-state exploration is accepted only above the declared closure floor; otherwise the explorer routes to full predictive state.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
