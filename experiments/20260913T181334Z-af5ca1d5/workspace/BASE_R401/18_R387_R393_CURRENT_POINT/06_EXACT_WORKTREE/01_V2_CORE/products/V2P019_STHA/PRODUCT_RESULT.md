# V2P019_STHA — Support-Tipped Holdout Audit

Composition: `FOUNDRY:P065 -> PARENT:R014_S781_S792_ACSA`.

Mechanism: SWTE support tipping gates ACSA-style protected holdout selection. If effective support falls below the declared floor, the audit abstains instead of treating the protected mean as stable.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
