# START HERE — LabAllCompass Full Current-Point Archive R393

This is the archive-of-record current through the **R392 product-authority promotion** and the **R393 fresh full-universe routing rebuild** on 2026-08-30. It is an additive update of the R386 rehydration archive: historical source and case material remain physically preserved while all R387→R393 code, products, tests, telemetry, authority receipts, routing universes, negative knowledge, and methodology changes are added as a new current-point layer.

## Read order

1. `02_CANONICAL_CURRENT_STATE.json` — current machine-readable authority.
2. `01_ARCHITECTURE_BLUEPRINT.md` — architecture plus R387→R393 visibility corrections.
3. `03_CHRONOLOGY_R1_R393.md` — historical chronology extended through this checkpoint.
4. `06_REGISTRY_PRODUCTS_AND_CATEGORIES.md` — exact taxonomy/count semantics.
5. `18_R387_R393_CURRENT_POINT/00_CURRENT_POINT_README.md`.
6. `18_R387_R393_CURRENT_POINT/02_CONVERSATION_AND_METHODOLOGY_DELTA.md`.
7. `18_R387_R393_CURRENT_POINT/03_PRODUCT_MECHANISM_LEDGER_R387_R392.jsonl`.
8. `18_R387_R393_CURRENT_POINT/05_R393_NEXT_FRONTIER.md`.
9. Run `python 09_VERIFY_ARCHIVE.py`.

## Authority rule

The historical scientific base remains **R12 / Registry455 / Products38 / Quality28** as provenance. Product authority has since advanced through explicit tested transitions. The current authority is **R392 / Registry455 / Products52 / Quality39**. Registry455 has not changed. `V2P047` remains quarantined.

R393 is **shadow routing only**: it rebuilt the full frontier under R392 authority and has not promoted V2P054 or any new product.

## Current control plane

- 310 reusable capabilities = 96 LCB + 69 Foundry parents + 145 Foundry executable compositions.
- 50 of the 69 parents are the historical Retro50; they are not an extra Quality count.
- 4,310 interaction nodes.
- 16,647 interaction edges = 52 completed + 16,537 inferred + 53 parent + 5 rejected-current-interface.
- 447 mechanics telemetry events; 447 exact current-suite matches; 0 unmatched; 52/52 suites calibrated.
- 16,594 persistent candidate rows; top-1000 is only an operational window.
- R393: 15,578 fresh/unadjudicated pairs → 649 mechanism clusters.

## Critical R388 visibility lesson

The Retro50 were already present. The Lab was missing interactions because `FOUNDRY_PARENT` provenance had been treated like semantic-family identity, suppressing parent↔parent composition. The repair exposed 890 previously invisible rank-compatible parent pairs. **Do not reintroduce this conflation.** The goal is neither raw count inflation nor artificial count suppression; the requirement is complete visibility followed by strict product-quality adjudication.

## Archive policy

`11_SOURCE_ARCHIVE/`, `12_CASE_LIBRARY/`, and `17_R386_CURRENT_POINT/` are preserved from the original R386 archive. New work is under `18_R387_R393_CURRENT_POINT/`. Recursive prior transport ZIPs are indexed by hash but not nested. Regenerable caches and one historical raw transcript byte-identical to the already-preserved R386 source copy are omitted and recorded in `13_OMITTED_REGENERABLE_OR_RECURSIVE_WRAPPERS.tsv`.
