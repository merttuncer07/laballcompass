# Visibility, Telemetry, Closure, and Regression Repairs — R387→R392

## Current certified numbers

- Registry families: **455**, unchanged.
- Capability reservoir: **310 = 96 LCB + 69 parents + 145 Foundry compositions**.
- Canonical V2 suites: **52**.
- Quality-distinct families: **39**.
- Operational canonical entity records: **362 = 310 capabilities + 52 V2 suites**.
- Interaction map: **4310 nodes / 16647 edges**.
- Relations: **52 completed / 16,537 inferred / 53 parent / 5 rejected-current-interface**.
- Mechanics telemetry: **447 events / 447 exact current-suite matches / 0 unmatched / 52 calibrated suites**.
- Persistent candidate universe: **16,594**, active **16,589**.
- Operational queue: **1,000** rows; not the graph boundary.
- Learning-eligible empirical campaign events: **0**.

## Repairs that must survive rehydration

### Dynamic suite closure
Control-plane projections must derive current physical/canonical suite sets from current authority/discovery. Historical R12 counts remain historical facts; they are not allowed to cap later physical state.

### Package-relative execution
Do not restore obsolete absolute `/mnt/data/...R385...` test dependencies. R387 corrected the new R386 suites to resolve dependencies from the package root.

### Exact-current-signature telemetry
A passing event from an older code/test signature cannot calibrate a changed suite. R387 superseded 64 stale events after portability edits; R389 explicitly superseded an early V2P050 pilot after hardening. Live telemetry must match current source/test fingerprint exactly.

### Provenance bucket ≠ semantic family
`FOUNDRY_PARENT` is a provenance/category label, not proof that all parents are equivalent. The old same-family guard hid 890 valid rank-compatible parent↔parent candidates. Preserve R388's split semantics.

### Full universe persistence
Persist all **16,594** native candidate rows. Top-1000 is a bounded operational queue only. A low queue rank must not erase an interaction from research memory.

### Auto-discover all direct product tests
Packaged regression must enumerate all current `V2P*/test_*.py` surfaces. Never restore a fixed numeric product range.

### Product artifact completeness
Executable-suite discovery is contract-driven. V2P053 demonstrated that code/tests alone are not enough if required product artefacts such as `PRODUCT_RESULT.md` are absent. Discovery must fail visibly rather than silently losing the suite.

### Historical closure future-proofing
A historical release test may assert its historical audit exactly, but it must not assert that no future authority can exist. R387/R388/R389/R390/R391 historical closures were adjusted to distinguish historical audit from current authority.

### Regression inheritance by byte identity only
Clean prior regression receipts can be inherited only if the corresponding source/artifact tree is byte-identical to the archive-of-record. Changed/new surfaces run fresh. R392 promotion proof is in `06_EXACT_WORKTREE/09_R392_NATIVE_ROUTING/R392_PROMOTION_REGRESSION_BUNDLE.json`.

## Evidence boundary

Mechanics telemetry and synthetic removal-control benchmarks certify deterministic executable behavior and internal-family distinctness under declared shells. They are not empirical learning, novel-theory proof, financial validation, deployment assurance, or real-world scientific validation.
