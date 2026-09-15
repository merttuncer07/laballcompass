# Product result — P001 DREW v0.1

**Route:** A — research / decision reliability stack  
**Parents:** ACSA + DLEW + TDSX + SCE + MDDC + optional MIFF  
**Promotion state:** `REAL_DATA_PILOT`  
**Result:** working standalone composition

## What materially changed

DLEW previously answered whether model rankings by prediction error and downstream decision loss
could differ. ACSA previously answered whether an adaptively selected candidate survived untouched
evaluation, but required a case-by-candidate loss matrix. DREW makes downstream decision regret the
selection-audit object directly. This closes an executable loop:

`raw predictions/outcomes/actions → casewise decision regret → adaptive-selection audit → protected candidate comparison`.

TDSX can then treat the decision-selection advantage itself as the black-box metric whose assumption
surface is explored. The other Route-A parents are preserved as typed evidence branches rather than
collapsed into a false common metric.

## Measured evidence

- Parent baseline: 69 parent test files, 271 tests, zero failures.
- New DREW tests: 8/8 pass.
- Synthetic adverse-shift benchmark: DLEW alone selects an in-search decoy; protected DREW audit
  exposes it. Fresh-final regret reduction after validation correction: **99.8976%**.
- Boundary case: when the selected candidate remains good, DREW reports survival rather than
  inventing a failure.
- Interface mismatch: candidate/output shape mismatch raises `ValueError`; no silent coercion.
- Real-data digits pilot: 27 classifiers; protected audit changes `knn_k3 → knn_k1`; fresh-final
  classification error changes **8/360 → 6/360**, a **25% relative reduction**.

## Limits / next pressure tests

The real-data improvement is only two final errors and one fixed split; it is evidence that the
composition operates on real data, not evidence of universal superiority. Next pressure tests should
repeat predeclared splits across several non-isomorphic domains and compare nested-CV / bootstrap
selection baselines. The SCE branch currently maps specification evidence but does not yet emit
holdout predictions, so **SCE → ACSA** remains an `INTERFACE` frontier rather than a claimed direct
composition.
