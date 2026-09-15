# V2P027_DRMPHA — Decision-Relevant Memory-Policy Holdout Audit

Composition: `PARENT:IM334_IM094_DRE -> FOUNDRY:P137`.

Mechanism: DRE orders which policy variants deserve protected audit using development-side uncertainty and leverage only. The protected holdout remains sealed during prioritization; selection is then evaluated only after the audit order is frozen.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
