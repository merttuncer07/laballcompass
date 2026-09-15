# EDSANP — Effective-Diversity-Gated Support-Aware Neutral Portfolio

Composition: `LCB-K019 EffectiveDiversityGuardV0 -> FOUNDRY:P003 SANP`.

Neutral mechanism:

`CLAIMED SUPPORT RELATION -> NOMINAL EVIDENCE MULTIPLICITY + DEPENDENCE -> EFFECTIVE INDEPENDENT COUNT -> ALLOW STRUCTURED SUPPORT PATH OR FALL BACK`

The adapter does not infer, repair, or prune the support mask. Every off-diagonal mask decision—both a claimed relation and a claimed absence—must have an explicit evidence group. K019-style equicorrelation accounting converts nominal multiplicity into effective independent count and aggregate variance inflation. If any off-diagonal mask decision lacks evidence or fails the declared gate, the whole structured SANP route is refused and ENPC is solved from raw sample covariance.

Passing the gate is not proof that the support graph is scientifically correct. It only prevents correlated evidence from being counted as if it were independent evidence for P003's external support assumption.
