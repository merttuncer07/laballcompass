# V2P025_DRFIAC — Decision-Relevant Firewalled Information Acquisition

Composition: `PARENT:IM334_IM094_DRE -> FOUNDRY:P057`.

Mechanism: DRE prioritization is applied only after FIAC removes suspect-source channels. The product selects the clean channel with the highest decision-relevant value rather than allowing a contaminated high-information channel to win.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
