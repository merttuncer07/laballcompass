# Registry, Capability, Product and Instrumentation Semantics — R385

## Correct entity hierarchy

- **Registry455**: canonical mechanism-family ontology. Do not increment for control-plane utilities or variants.
- **96 LCB kernels**: reusable executable kernel capabilities.
- **69 Foundry parents**: reusable parent capabilities.
- **145 Foundry executable compositions**: executable composition modules in the Foundry universe. These are not automatically product families.
- **310 canonical capabilities**: 96 + 69 + 145.
- **Products38**: completed executable V2 composition suites.
- **Quality28**: distinct product-family reporting after anti-iteration-inflation review.
- **348 operational entities**: 310 capabilities + 38 V2 product suites. Quality28 is a grouping, not another 28 entities.

## Why the old `202 products` count was misleading
R384's genealogy contained 38 V2 suites + 145 Foundry compositions + only 19 Foundry parents = 202 rows. It omitted 50 other Foundry parents and all 96 LCB kernels. It therefore mixed taxonomy levels and was not a complete inventory. That ledger is preserved as a superseded historical artifact.

## What happened to the 145 Foundry compositions?
They did not simply “go nowhere.” At R12 their primary graph state is:

- 22 promoted into at least one completed V2 composition edge.
- 35 executable and still represented on the inferred Foundry frontier, without direct V2 promotion.
- 9 have explicit Foundry-parent lineage but no direct V2 completed edge.
- 79 are dormant registered executable compositions at the R12 interaction-map snapshot. **Dormant does not mean failed.** It means no completed/inferred/parent/rejected graph role was active for that node in that snapshot.
- A few nodes have mixed parent/inferred/rejected roles; the exact multi-role state is preserved per entity in `05_ENTITY_GENEALOGY.jsonl`.

## Interaction map
R12 graph: **4310 nodes / 1057 edges**.

- 4000 primitive nodes
- 310 capability nodes
- 38 `COMPLETED_COMPOSITION` edges
- 962 `INFERRED_CANDIDATE` edges
- 53 `PARENT_OF` edges
- 4 `REJECTED_CURRENT_INTERFACE` edges

These relation types are epistemically different and must not be collapsed into one edge score.

## Telemetry placement
R12 telemetry is topology-bound:

- 316 total experiment telemetry events
- 38 completed edges instrumented
- 38 V2 products indexed
- 38 problem shells indexed
- 38 tests indexed
- 38 current suites conservatively calibrated
- 0 unmatched events

Each completed interaction edge can carry `telemetry_events`; the telemetry registry additionally indexes the same evidence `by_edge`, `by_product`, `by_shell`, and `by_test`. Calibration produces conservative reliability, compute-cost and resolution-by-axis estimates. These values hydrate Foundry/experiment routing; they do not themselves constitute scientific validation.

## Identity relations remain separate
Proposal identity / motif equivalence / full mechanism equivalence / product-family equivalence are different relations. The Quality28 collapse must never be used to erase executable or genealogical history.

Exact registries, queues, telemetry ledger, interaction map, composition benchmarks and source code are in `11_SOURCE_ARCHIVE/R001_R012_CANONICAL_R12_FULL`.


# R386 product-overlay accounting

Canonical counts remain Registry455 / Products38 / Quality28. R386 adds a separately-authorized candidate layer:

- 10 shadow executable suites built: V2P039–V2P048.
- 9 are native-queue promotable executable suites.
- 6 are internal distinct-family candidates: V2P039, V2P040, V2P041, V2P042, V2P043, V2P046.
- 3 are executable family variants: V2P044, V2P045, V2P048.
- V2P047 is quarantined exploratory/out-of-native-queue.
- Candidate accounting if explicitly accepted: Products47 / Quality34.
- Registry455 is unchanged.

The R386 quality audit and exact per-product mechanisms/removal comparators/prior-art boundaries live in `17_R386_CURRENT_POINT/01_SWEEP_LEDGER_AND_SCRIPTS/R386_PRODUCT_QUALITY_AUDIT.json`.

**R386 promotion warning:** Products47 / Quality34 is candidate accounting only. It is not eligible for canonical promotion until the inherited R12 closure contracts are deliberately updated or wrapped for overlay semantics and the complete regression passes.

# Current R392/R393 accounting update

The historical R12 counts above remain valid as historical audit. Current explicit product authority is now:

- **Registry455** — unchanged canonical mechanism-family ontology.
- **96 LCB kernels + 69 Foundry parents + 145 Foundry executable compositions = 310 reusable capabilities**.
- **Retro50** — 50 of the 69 parent capabilities; a composition reservoir, not an automatic product-family count.
- **Products52** — current canonical executable V2 composition suites under R392 authority.
- **Quality39** — current distinct-family collapse of those 52 suites.
- **362 current operational canonical entities = 310 capabilities + 52 suites**. Quality39 remains a grouping, not 39 extra entities.
- `V2P047` is quarantined and excluded from Products52.

## Product-authority progression

- R12 historical: 38 / 28
- R387: 47 / 34
- R388: 48 / 35 (`V2P049`)
- R389: 49 / 36 (`V2P050`)
- R390: 50 / 37 (`V2P051`)
- R391: 51 / 38 (`V2P052`)
- R392 current: 52 / 39 (`V2P053`)

## Current interaction/instrumentation map

R392 graph: **4310 nodes / 16647 edges**:

- 4000 primitive nodes
- 310 capability nodes
- 52 completed-composition edges
- 16537 inferred candidate edges
- 53 parent-of edges
- 5 rejected-current-interface edges

The full Foundry candidate universe is **16594 rows**. Its top-1000 queue is only an operational window and must never be used as the graph boundary.

## Retro50 correction

The Retro50 were never supposed to be added blindly to Quality39. The important finding was that their interactions had been partially invisible. All 50 were already among the 69 parent records, but a shared provenance label caused a same-family guard to suppress parent↔parent candidates. R388 corrected this and exposed 890 compatible directed parent pairs. Product quality and graph visibility are separate gates.

## Telemetry

Current mechanics telemetry has **447 events**, all 447 exact current-suite matches, 52/52 suites calibrated, 0 unmatched. These events calibrate executable mechanics/placement; they are not empirical-learning or real-world validation evidence.



# Final retirement accounting update — R394 through R398 candidate

The R392/R393 section above remains the last **byte-complete exact worktree** accounting. The conversation continued with explicit tested product-authority promotions whose late ephemeral source bytes were later lost in a runtime remount. Preserve both levels:

- R394 logical authority: Products53 / Quality40 (`V2P054 CADSBC`)
- R395: 54 / 41 (`V2P055 DLSAICC`)
- R396: 55 / 42 (`V2P056 SACRDSBC`)
- R397: **56 / 43** (`V2P057 REOC`) — final logical canonical authority
- R398: `V2P058 SACATRC` candidate overlay only; would be 57 / 44 if a fresh replay completes promotion, but **NOT PROMOTED** in this handoff.

Observed R398 candidate control plane: 57 completed physical/candidate edges, 16,532 inferred, 53 parent, 5 rejected-current-interface = 16,647 total. Mechanics ledger reached 516/516 exact matches, 57/57 calibrated, 0 unmatched. These are receipt-supported state facts, not an exact-byte worktree claim and not empirical validation.

The last exact embedded worktree remains R392 with V2P001–V2P053. Late product contracts and reference reconstructions are under `19_R394_R398_FINAL_RETIREMENT_DELTA/`.
