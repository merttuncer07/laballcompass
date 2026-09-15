# R388 authority transition

R388 repairs a visibility defect in the native Foundry interaction graph and promotes one independently quality-gated executable composition.

## Why R388 existed

All 50 Retro products were already physically present and all 50 were already represented among the 69 `FOUNDRY_PARENT` records. The defect was not missing files or missing parent records. `build_core_v2_foundry.py` treated the shared `FOUNDRY_PARENT` provenance label as a semantic family and suppressed every same-family composition before native ranking. This hid parent→parent interactions, including Retro→Retro and Retro↔current-parent pairs.

R388 separates semantic-family suppression from the `FOUNDRY_PARENT` provenance bucket. The 69 parents can now reach native `rank_composition` against one another; incompatible pairs may still produce no candidate and all candidates remain subject to normal interface, ancestry, duplicate, usefulness, and quality adjudication.

## Visibility repair

- Foundry parent records: 69.
- Retro parent records: 50.
- Current non-Retro parent records: 19.
- Directed parent pairs before compatibility: 4,692.
- Previously hidden native-rank-compatible parent→parent pairs made visible: 890.
  - Retro→Retro: 422.
  - Retro→current parent: 250.
  - current parent→Retro: 140.
  - current parent→current parent: 78.
- Full ranked candidate universe: 16,594 rows.
- Active candidates: 16,589.
- Operational queue remains bounded at 1,000 rows, but the full universe is persisted in `CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl` so lower-ranked candidates are no longer invisible.

This is a graph-visibility result, not a novelty claim.

## Product result

R388 admits `V2P049 SACAPL = R037 SACPS → R041 CAPL` as one new distinct executable composition family.

The mechanism is support-aware covariance changing CAPL's policy risk-objective geometry while CAPL's feasible set, constraints, optimizer shell, transaction-cost shell, and action map remain fixed. The mechanism-removing control replaces support-aware covariance with raw sample covariance. The candidate has an explicit collapse region and abstention/fallback boundary; its evidence remains deterministic/synthetic mechanics evidence, not market validation.

`V2P050 SCIG` remains shadow-only for subsequent adjudication and is not part of R388 authority.

## Canonical authority after promotion

- Registry-family authority: 455, unchanged.
- Executable V2 suites: 48.
- Quality-distinct V2 product families: 35.
- V2P047: quarantined and not counted.
- Mechanics telemetry: 398 events / 398 exact current-suite matches / 0 unmatched.
- Calibrated current suites: 48/48.
- Interaction-map completed-composition edges: 48.
- Rejected-current-interface edges: 5.
- Empirical learning-eligible campaign events: 0.

Historical R12 `38/28`, R386 `47/34` candidate accounting, and R387 promotion records remain immutable provenance layers.

## Promotion gate

The monolithic packaged runner returned process exit `0` but emitted an empty redirected stdout artifact. R388 does not treat that empty artifact as sufficient evidence. Promotion instead uses `R388_PROMOTION_REGRESSION_BUNDLE.json`, which binds independent terminal receipts for:

- Foundry regression: 214/214 parent/product test files passed; 806 tests counted.
- Direct V2 auto-discovery: 48/48 physical V2 suite test files passed.
- Core/search/relevance/experiment/closure surfaces: 12/12 passed.

The anomaly itself is preserved in `R388_MONOLITHIC_RUNNER_ANOMALY.json`.

## Continuation rule

Continue from the full persisted candidate universe, not only the top-1000 operational queue. Carry forward every existing disposition. A fresh row means unadjudicated, not novel. Do not infer product status from rank, compatibility, telemetry presence, or a high V2P identifier. New product-family promotion still requires a non-additive failure/mechanism contribution, nearest-family and ancestry checks, mechanism-removing comparator, fail-closed boundary, deterministic tests/benchmark, telemetry closure, and explicit authority transition.
