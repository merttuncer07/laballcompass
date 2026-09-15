# P005 — CARF v0.1

Certificate-Aware Reduction Foundry.

CARF routes a reduction request by the property that must survive compression. It treats preservation certificates as typed objects rather than interchangeable statements that a model is "reduced safely".

Supported requirement families:

- full input-output behavior: CORMA -> BRED;
- protected output trajectory: CORMA -> TWMR;
- threshold action invariance: TSRC;
- causal target estimation: OTE;
- closed aggregate Markov dynamics: SALC;
- bounded decision regret: DSBC;
- observable predictive/update closure: PSCT.

The first cross-family guard is executable: a TSRC action-preserving feature deletion is re-audited through OTE before anyone is allowed to treat it as causal-sufficient.
