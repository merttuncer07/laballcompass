# Reproducibility and Bootstrap — R393 Full Current Point

## Rehydrate in this order

1. Read `00_START_HERE.md`.
2. Read `02_CANONICAL_CURRENT_STATE.json`.
3. Read `01_ARCHITECTURE_BLUEPRINT.md`.
4. Read `03_CHRONOLOGY_R1_R393.md`.
5. Read `18_R387_R393_CURRENT_POINT/00_CURRENT_POINT_README.md` and its delta/mechanism/frontier files.
6. Run `python 09_VERIFY_ARCHIVE.py` from the archive root.
7. Treat `18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/01_V2_CORE/CURRENT_PRODUCT_AUTHORITY.json` as current product authority.

## Historical source

`11_SOURCE_ARCHIVE/`, `12_CASE_LIBRARY/`, and `17_R386_CURRENT_POINT/` preserve the R386 archive-of-record. Do not rewrite them to look like R392. Historical audit and current authority are intentionally separate.

## Current executable tree

`18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/` contains current code/tests/results through R392 promotion plus R393 routing. Regenerable caches and the byte-identical raw historical transcript duplicate are omitted. The historical raw transcript remains available in the preserved R386 source tree.

## Reproduce current state

From `18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/01_V2_CORE/`:

- inspect `CURRENT_PRODUCT_AUTHORITY.json`;
- inspect `generated_search/INTERACTION_MAP_R12.json` and `generated_search/EXPERIMENT_TELEMETRY_INDEX_R12.json`;
- inspect `generated_v2_foundry/CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl` and the bounded composition queue;
- use `refresh_lab_state.py` to rebuild derived state if needed;
- direct product regression must auto-discover every current `products/V2P*/test_*.py` surface.

Do not recreate old absolute R385 `/mnt/data/...` dependencies. R387 fixed those portability leaks.

## Continue research

Do not manually choose a favorite idea when the native router has usable candidates. Start from `18_R387_R393_CURRENT_POINT/05_R393_NEXT_FRONTIER.md` and `06_EXACT_WORKTREE/10_R393_NATIVE_ROUTING/`.

The R393 cluster ranking is triage only. For any representative, require code-level non-additivity, collision review, mechanism-removing control, working/collapse/failure regions, product artefact completeness, direct tests, current-signature telemetry, closure, and promotion regression before authority changes.

## Regression inheritance

Prior clean regression receipts may be inherited only after byte-tree identity against the prior archive-of-record. If any byte changes, rerun that affected surface. Never infer a PASS from a timeout or missing terminal receipt.

## Evidence boundary

Mechanics telemetry/synthetic benchmarks are not empirical-learning evidence and do not establish financial/scientific/deployment validity.


# Final retirement replay note

For byte-reproducible execution, bootstrap from `18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE` (R392 exact). The R394–R398 product source trees are not byte-reproducible from this runtime because the unsurfaced ephemeral directories were lost after remount. Use the recovered contracts/reference modules to rebuild, then rerun their direct/sensitivity/telemetry/closure/promotion gates. Do not copy logical authority counts into an exact worktree without replay.
