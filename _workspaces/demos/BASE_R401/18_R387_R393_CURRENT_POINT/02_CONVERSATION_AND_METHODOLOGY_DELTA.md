# R387→R393 Conversation, Methodology, and Architecture Delta

This file records the changes made after the R386 rehydration archive was loaded. It intentionally records corrections and false starts as provenance rather than rewriting them out of history.

## 1. R387 — close the R386 candidate overlay correctly

R386 physically contained a 47-suite candidate overlay, but three control-plane projections still encoded the old 38-suite assumption: interaction topology completion, Foundry queue hydration, and campaign/mechanics memory. The inherited R12 closure also asserted that physical/current suite count must stay at 38.

R387 repaired the projections rather than changing the scientific registry. The historical R12 audit remained 38/28; the candidate layer became 47 executable suites / 34 distinct product families. After full regression returned a clean terminal receipt, an explicit product-authority transition promoted R387. Registry455 stayed unchanged.

A portability defect was also found: eight of the nine new R386-promotable suites had tests bound to obsolete absolute `/mnt/data/...R385...` paths. Their harnesses were made package-relative. Because this changed exact test fingerprints, stale mechanics telemetry was not reused. Sixty-four affected R386 events were preserved as superseded provenance and replaced with 64 fresh R387 exact-shell events, keeping the live ledger at 388 rather than inflating it to 452.

## 2. Screenshot intervention — the Retro50 were not a count problem; they exposed a visibility bug

The user supplied screenshots (`07_CONVERSATION_EVIDENCE/`) that prevented a serious conceptual loss. We were close to concluding that the retro frontier had been exhausted. Direct code inspection showed a subtler reality:

- all **50 Retro products already existed** among the 69 `FOUNDRY_PARENT` records;
- 19 additional non-Retro parent records completed the 69;
- several canonical V2 products already used Retro parents;
- the real blind spot was that every parent carried the same broad `FOUNDRY_PARENT` provenance/family label, and the generator's same-family guard used that label as if it meant semantic equivalence.

Therefore parent↔parent composition was suppressed. Fixing that semantic/provenance conflation exposed **890 previously invisible native rank-compatible directed parent pairs**: 422 Retro→Retro, 250 Retro→current-parent, 140 current-parent→Retro, and 78 current-parent→current-parent.

The user's correction was explicit: **the issue is not preventing count inflation; the issue is not missing real interactions.** That principle now governs the visibility layer.

## 3. R388 — topology repair, persistent universe, V2P049

R388 separated provenance bucket from semantic-family equality, opening the parent↔parent surface without duplicating the Retro50. It also fixed a second visibility issue: the top-1000 Foundry queue had been treated too much like the graph. R388 persisted the full **16,594-row candidate universe**; top-1000 became explicitly only an operational priority window.

A third visibility fix changed packaged regression from a hard-coded direct-test range (historically V2P001–V2P013) to automatic discovery of every current `V2P*/test_*.py` surface.

R388 promoted `V2P049 SACAPL = R037 SACPS → R041 CAPL`, in which support-aware covariance changes CAPL's quadratic risk geometry inside the optimizer. Current product authority became 48/35.

## 4. R389 — V2P050 and exact-current-signature telemetry

`V2P050 SCIG = R037 SACPS → IM445/IM085 CSID` repairs CSID evidence-family equivalence before coverage multiplication/portfolio search using support-aware covariance structure. An early 10-case pilot existed, but later hardening expanded/changed the direct surface. The old pilot was explicitly superseded; the final current signature used 13 direct cases. This established a rule: **telemetry calibration follows the current exact code/test signature, never an older successful pilot.** R389 promoted to 49/36.

## 5. R390 — V2P051 SACDLW

`V2P051 SACDLW = R037 SACPS → R044 DLEW` injects support-aware covariance before DLEW finite-action argmax and oracle-regret calculation. It passed removal/collapse controls and had a conditional, not universal, sensitivity region. R390 promoted to 50/37.

## 6. R391 — V2P052 REICAPL

`V2P052 REICAPL = P028 REIS → R041 CAPL` converts REIS posterior×consequence safeguard selection into heterogeneous per-asset feasible caps before constrained optimization. It differs from V2P049 (risk objective) by changing the feasible-set geometry. Working benefit is conditional; missing record↔asset semantic alignment fails closed. R391 promoted to 51/38.

R391 also removed a release-visibility trap in state refresh: overlay discovery became dynamic instead of stopping at a hard-coded release list. Historical closure tests were made future-release-safe while preserving their exact historical audit counts.

## 7. R392 — V2P053 SWCAPL and product-artifact completeness

`V2P053 SWCAPL = P090 SWDL → R041 CAPL` applies externally justified source→target importance weights and OWS support gating directly inside CAPL's realized-action training objective before constrained optimization. It changes the learned policy. Uniform weights collapse exactly to the removal control; fragile effective support fails closed. The sensitivity sweep is explicitly conditional: source-like targets can be harmed by target-shift weights, while sufficiently shifted targets show consistent gains in the synthetic shell.

A new visibility/productization defect was caught here: code/tests/sensitivity files existed, but the candidate lacked `PRODUCT_RESULT.md`, so executable-suite discovery did not count it. The missing product artefact contract was completed before telemetry. Pre-telemetry state then correctly showed 52 observed / 51 calibrated; a fresh 12-case exact-shell pilot brought the ledger to 447 and 52/52 calibration. R392 promoted to **52 executable / 39 distinct families**.

## 8. Provenance-preserving regression inheritance

From R390 onward, unchanged historical surfaces are not blindly rerun for hours and are not blindly trusted either. A prior clean regression receipt may be inherited **only after byte-tree identity is proven** against the prior archive-of-record. Any changed byte rejects inheritance for that surface; changed/new surfaces run fresh. Promotion bundles record both inherited byte-identity proof and fresh-test receipts.

At R392: the 51 prior canonical suites were byte-identical across 412 files, Foundry was byte-identical across 1305 files, V2P053 ran fresh 12/12, and state-sensitive regression ran fresh 16 surfaces / 142 tests / 0 failures.

## 9. R393 — clean next frontier, no premature product

After R392 promotion, the full universe was reconciled again from canonical authority. R393 sees 15,578 genuinely fresh/unadjudicated edges and 649 workload-triage mechanism clusters. There is no surviving shadow suite and no R393 promotion yet. The next step is code-level adjudication of diverse representatives; ranking is not a product claim.

## Methodology retained

The durable research loop is:

`current authority → unresolved failure inventory → closure/impossibility → structured retrieval → complete interaction visibility → typed identity/collision → native ranking → diverse cluster triage → code-level non-additivity → mechanism-removal control → working/collapse/failure regions → direct tests → exact-shell mechanics telemetry → control-plane closure → regression/byte-identity proof → explicit product-family adjudication → explicit authority promotion`.

Mechanics telemetry remains **non-learning evidence**. It proves executable contract calibration, not scientific novelty, financial edge, deployment readiness, or real-world validity.
