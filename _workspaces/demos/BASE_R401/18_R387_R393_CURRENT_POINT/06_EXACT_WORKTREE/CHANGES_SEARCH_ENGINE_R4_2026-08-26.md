# LabAllCompass Search/Reflexive Engine R4 changes — 2026-08-26

R4 adds a leakage-aware experiment-selection layer after R3 retrieval/composition/relevance learning.

## Added

1. `01_V2_CORE/experiment_selector.py`
   - explicit uncertainty axes;
   - explicit test-resolution matrix;
   - decision-progress-per-compute routing;
   - blind-axis reporting;
   - compute ceilings;
   - protected-validation exclusion;
   - frozen plan fingerprints;
   - next-round-only outcome updates;
   - mandatory calibration provenance;
   - fail-closed treatment of unknown or unadjusted measurement backreaction.

2. Operational entry points
   - `select_next_experiment.py`
   - Core V2 `choose_lab_next_experiment()`
   - Core V2 `audit_foundry_experiment_readiness()`
   - Search→Foundry packet experiment gate.

3. Factory schema integration
   - `build_core_v2_foundry.py` now emits `decision_id`, `uncertainty_axes`, `test_channels`, and `experiment_routing_status` on every queue row;
   - unknown fields remain null instead of being guessed;
   - fixed stale packaged Foundry source path so the builder regenerates from `02_FOUNDRY_ALL_PRODUCTS/audit/PRODUCT_EVIDENCE_INVENTORY.jsonl`.

4. Verification artifacts
   - `generated_search/EXPERIMENT_READINESS_AUDIT_R4.json`
   - `generated_search/EXPERIMENT_SELECTOR_SYNTHETIC_REPLAY_R4.json`
   - `generated_search/CRYPTO_V1_FOUNDRY_SEARCH_PACKET_R4.json`

## Current factory readiness result

- composition queue rows: 1,000
- ready for quantified experiment routing: 0
- not ready: 1,000

This is intentional. Existing queue rows do not contain calibrated uncertainty/test/compute telemetry.

## Synthetic mechanics replay

A five-axis synthetic decision with declared test calibrations routes:

`T_C -> T_AB -> T_DE`

- unresolved mass: 5.0 -> 0.4
- selected declared compute: 6.0
- exhaustive single test declared compute: 20.0
- protected validation selected: false
- unquantified test selected: false

These numbers validate routing mechanics only; they are not empirical Lab performance claims.

## Search behavior preservation

Under the existing generation-1 Crypto relevance snapshot, the mechanism anchors remain:

- P137 MPHA #1
- LCB-K071 GuaranteeTransportGate #3
- LCB-K089 SelectionAwareReferenceLaw #9
- LCB-K011 MemoryKernelClosure #12
- LCB-K069 PredictableVarianceAlarm #17

The R4 Crypto packet correctly reports experiment selection as `NOT_READY_WITHOUT_DECLARED_EXPERIMENT_CONTRACT`; R4 does not invent test value from the problem prose.

## Verification

Focused Core/Foundry/search/relevance/experiment suite: **46/46 PASS**.
