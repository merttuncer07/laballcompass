# DREW v0.1 — Decision Reliability Evaluation Workbench

DREW is the first Product Interaction Foundry composition. It combines six existing standalone
parents without silently changing them: ACSA, DLEW, SCE, TDSX, MDDC, and optional MIFF.

The central new executable adapter is **DLEW → ACSA**. Raw model predictions are converted into a
case-by-candidate matrix of downstream decision regret using DLEW's exact sequential action and
transaction-cost semantics. ACSA then audits whether the candidate chosen on the search segment
survives a protected evaluation segment. This detects a failure mode that DLEW alone cannot detect:
a model can win by downstream loss on the same adaptive search sample and still be a selection
artifact.

A second directed adapter is **DLEW → TDSX**. TDSX can search assumption surfaces over the difference
between validation regret from decision-loss selection and ordinary RMSE selection, locating where
the apparent decision advantage changes sign.

SCE, MDDC, and MIFF remain native evidence branches rather than being coerced into a common scalar:
SCE maps declared specification choices; MDDC exposes metric/decision ranking inversions; MIFF can cut
suspect feedback paths into protected evaluation. DREW returns evidence flags but does not use them as
an automatic idea-killing gate.

## Primary API

- `decision_regret_matrix(...)` — DLEW-compatible raw predictions → ACSA-compatible loss matrix.
- `audit_decision_model_selection(...)` — DLEW selection + protected ACSA audit.
- `explore_decision_selection_surface(...)` — TDSX over DLEW's downstream selection advantage.
- `run_reliability_workbench(...)` — optional full Route-A orchestration while preserving parent results.

## Evidence so far

Parent baseline before construction: **69 files / 271 tests / 0 failures**.

DREW tests: **8/8 passing**, including parent-semantic equivalence, adaptive-decoy exposure, a
no-shift boundary case, prediction-vs-decision ranking divergence, a TDSX tipping surface, a full
six-parent route, and explicit interface-mismatch rejection.

Synthetic adverse-shift benchmark: both search-RMSE and DLEW-alone selected `adaptive_decoy`; protected
DREW audit selected `stable_decision`. On a fresh final segment, mean decision regret fell from
`0.0152271` to `0.0000155899`, a **99.8976% relative reduction**. This is a deliberately adversarial
construction and is not real-world performance evidence.

Real-data pilot: scikit-learn handwritten-digits data, fixed seed `20260825`, 27 candidate models,
and separate fit/search/protected/final segments. Search decision loss and RMSE both selected
`knn_k3`; protected evaluation preferred `knn_k1`. Fresh-final error was **8/360 (2.222%)** for the
search winner and **6/360 (1.667%)** for the protected winner, a **25% relative reduction**. Selection
bootstrap fragility was `0.554`. This is one fixed-seed dataset pilot, not a general-performance claim.

## Run

```bash
python -m unittest -v test_drew.py
python benchmark_route_a.py
python real_data_pilot_digits.py
```

See `PARENT_PROVENANCE.md` for exact source snapshots.
