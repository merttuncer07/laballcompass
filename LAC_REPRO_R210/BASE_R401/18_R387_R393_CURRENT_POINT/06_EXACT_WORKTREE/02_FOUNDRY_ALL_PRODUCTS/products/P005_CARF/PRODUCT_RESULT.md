# P005 result — CARF v0.1

Promotion state: **WORKING_COMPOSITION / CERTIFICATE-SCOPE ROUTER**.

Tests: **4/4 passing**.

Primary synthetic certificate-mismatch benchmark:

- TSRC deletes `confounder` while retaining `decision_signal`;
- observed threshold-action changes after deletion = **0**;
- full OTE target = **1.97772** with standard error **0.01388**;
- OTE after the action-safe deletion = **3.44348**;
- target drift = **+1.46576**, equal to **105.6 full-model standard errors**.

The product therefore refuses to promote an action-margin certificate into a causal-sufficiency certificate.

Linear-system comparison also demonstrates why the routing target matters:

- CORMA reports the demonstration system as reducible;
- BRED selects order 1 under the global I/O error budget;
- TWMR separately selects `state_0` for the protected target output with **0 target-relative error**.

CARF does not declare one reduction method globally best. It records which property is protected and explicitly states what inference is not justified by that certificate.

Evidence label: **synthetic benchmark; certificate-scope demonstration, not real-world validation**.
