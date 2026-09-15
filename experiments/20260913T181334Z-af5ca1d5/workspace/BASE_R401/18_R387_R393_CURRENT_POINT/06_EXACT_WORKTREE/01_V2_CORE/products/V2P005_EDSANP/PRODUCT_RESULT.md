# V2P005 EDSANP — development adapter result

Composition: LCB `EffectiveDiversityGuardV0` + Foundry `P003 SANP`.

Status: **WORKING_COMPOSITION / DEVELOPMENT_ADAPTER_EVIDENCE**.

The bridge is intentionally narrow. P003 accepts a caller-supplied support mask but explicitly does not certify that the mask is scientifically correct. K019 does not certify the mask either. It only audits the multiplicity of evidence offered for every off-diagonal mask decision, including both claimed relations and claimed absences, under its equicorrelation shell.

For each off-diagonal mask decision, `n_eff = n / (1 + (n-1)rho)`. The structured P003 path is allowed only when every off-diagonal decision has explicit evidence, sufficient effective independent count, and aggregate variance inflation below the declared ceiling. Otherwise the adapter fails closed to raw-covariance ENPC without editing the mask.

Frozen deterministic boundary cases include: nominal n=100 with rho=0.05 fails a minimum effective count of 20 despite 100 nominal sources; n=100 with rho=0.001 passes; n=200 with rho=0.009 is individually below a 0.01 pairwise threshold but has collective variance inflation 2.791 and is rejected by a 2.0 ceiling.

This is development adapter evidence only. Equicorrelation, evidence-group construction, support truth, and real-world risk improvement remain external scientific/modeling claims.
