# LabAllCompass R393 Current Point — Read This After the Outer START_HERE

This directory is the additive R387→R393 layer placed on top of the original R386 archive-of-record. It exists so a new model or human collaborator can reconstruct the exact current state without flattening historical authority.

## Current authority

- Historical scientific base: **R12 / Registry455 / Products38 / Quality28**.
- Current explicit product authority: **R392 / Registry455 / Products52 / Quality39**.
- Current research revision: **R393 shadow routing**; no R393 product has been promoted.
- Registry455 remains unchanged.
- `V2P047` remains quarantined and is not part of Products52.
- Telemetry: **447/447 exact-shell**, **52/52 calibrated**, **0 unmatched**.
- Interaction topology: **16647 edges = 52 completed + 16,537 inferred + 53 parent + 5 rejected-current-interface**.
- Persistent Foundry candidate universe: **16,594** rows; the top-1000 queue is only an operational window.
- R393 fresh frontier: **15,578 unadjudicated edges / 649 mechanism clusters**.

## Read order inside this layer

1. `01_CURRENT_POINT_STATE.json`
2. `02_CONVERSATION_AND_METHODOLOGY_DELTA.md`
3. `03_PRODUCT_MECHANISM_LEDGER_R387_R392.jsonl`
4. `04_VISIBILITY_TELEMETRY_AND_REGRESSION_REPAIRS.md`
5. `05_R393_NEXT_FRONTIER.md`
6. `06_EXACT_WORKTREE/01_V2_CORE/CURRENT_PRODUCT_AUTHORITY.json`
7. `06_EXACT_WORKTREE/10_R393_NATIVE_ROUTING/R393_FULL_VISIBILITY_AUDIT.json`
8. `06_EXACT_WORKTREE/10_R393_NATIVE_ROUTING/R393_FULL_CLUSTER_SCREEN.json`
9. Outer `09_VERIFY_ARCHIVE.py`.

## Exact-worktree note

`06_EXACT_WORKTREE/` is the current R392/R393 working tree with only regenerable caches and one **byte-identical historical raw transcript duplicate** omitted. The omitted raw transcript already exists under the preserved R386 source archive and its SHA-256 identity is recorded in `13_OMITTED_REGENERABLE_OR_RECURSIVE_WRAPPERS.tsv`. Code, tests, promotion receipts, telemetry, candidate-universe files, routing ledgers and benchmark outputs are retained.

The inner `HANDOFF.md` / `00_START_HERE.md` are historical checkpoint documents accumulated during R388–R391 and may state an older authority. **Outer archive metadata and `CURRENT_PRODUCT_AUTHORITY.json` are authoritative.**
