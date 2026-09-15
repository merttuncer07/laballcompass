# V2P053 SWCAPL — SHADOW RESULT

`FOUNDRY:P090 SWDL -> PARENT:R041 CAPL`

Non-additive operator under test: externally justified source-to-target importance weights and the P090 OWS support gate reweight CAPL's realized-action training objective *before* constrained policy optimization. The removal control keeps the same optimizer, data, seed and constraints but restores uniform observation weights.

Working-region evidence is conditional: the declared target shift must be real and the supplied weights correct. Source-like validation under target-shift weights is an explicit failure region; fragile ESS fails closed.

Status: **R392 shadow only; not canonical.** Promotion requires current-signature exact-shell telemetry, closure, regression and explicit authority transition.
