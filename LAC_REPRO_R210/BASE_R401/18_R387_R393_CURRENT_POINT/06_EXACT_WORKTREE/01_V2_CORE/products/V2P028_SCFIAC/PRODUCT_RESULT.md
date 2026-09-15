# V2P028_SCFIAC — Support-Constrained Firewalled Information Acquisition

Composition: `PARENT:R037_SUPPORT_COVARIANCE_SACPS -> FOUNDRY:P057`.

Mechanism: SACPS support validity is applied before FIAC information ranking. Channels that are clean but unsupported are removed alongside suspect channels, preventing a high nominal information score from escaping either safety boundary.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
