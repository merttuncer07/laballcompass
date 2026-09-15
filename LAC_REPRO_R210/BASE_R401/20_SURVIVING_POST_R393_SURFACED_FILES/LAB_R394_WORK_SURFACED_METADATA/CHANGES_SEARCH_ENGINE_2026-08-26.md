# SUPERSEDED BY R2

This file records the first flat-search integration for provenance. The active search design and verification are in `CHANGES_SEARCH_ENGINE_R2_2026-08-26.md` and `01_V2_CORE/SEARCH_ENGINE_INTEGRATION.md`. Do not use the old 19-test / 5,893-evaluation figures as the current engine state.

# LabAllCompass V2 — search-engine integration changes

Date: 2026-08-26

## Intent correction

The supplied stable-decision-reuse mechanism was interpreted as a search-engine primitive, not as code to
transplant. The donor implementation is not imported or required by the integrated engine.

## New engine behavior

Repeated Lab retrieval is modeled as a top-k selection boundary:

`QUERY CHANGE -> DEPENDENCY INDEX -> SCORE-MOVEMENT INTERVALS -> TOP-K BOUNDARY CERTIFICATE -> REUSE OR SELECTIVE EXACT RESCORE`

The engine keeps exact cached document scores and cumulative conservative movement bounds. Query features
map to dependent documents through inverted indexes. The ordered shortlist is reused only when interval
separation certifies that membership and ordering cannot change. Otherwise only the competitive frontier
is exactly rescored; structural top-k changes fail closed to full search.

## Files added

- `01_V2_CORE/lab_search_engine.py`
- `01_V2_CORE/build_search_corpus.py`
- `01_V2_CORE/search_lab.py`
- `01_V2_CORE/SEARCH_ENGINE_INTEGRATION.md`
- `01_V2_CORE/test_lab_search_engine.py`
- `01_V2_CORE/test_search_corpus_integration.py`
- `01_V2_CORE/benchmark_lab_search_engine.py`
- `01_V2_CORE/search_data/LABALLCOMPASS_CANONICAL_INVENTORY_4000.tsv`
- `01_V2_CORE/generated_search/LAB_SEARCH_CORPUS.jsonl`
- `01_V2_CORE/generated_search/LAB_SEARCH_CORPUS_COUNTS.json`
- `01_V2_CORE/generated_search/LAB_SEARCH_ENGINE_BENCHMARK.json`

## Files changed

- `01_V2_CORE/core_v2.py`: adds `build_catalog_search_engine()` as the supported Core V2 entry point.
- `01_V2_CORE/START_HERE.md`
- `00_START_HERE.md`
- `PACKAGE_MAP.md`

## Corpus

- executable/product capability records: 310
- canonical primitives: 4,000
- total search documents: 4,310

## Verification

Focused engine/interface regression: 19/19 tests passed.

Actual-corpus deterministic replay:

- query updates: 60
- top-k: 20
- mismatches versus naive full exact search: 0
- naive exact score evaluations including initial search: 262,910
- integrated engine exact score evaluations including initial search: 5,893
- exact score-evaluation reduction: 97.7585%
- mean exact rescoring after initialization: 26.383 documents/update

This is a search-compute result for the declared scoring function. It is not evidence that the scoring
function is scientifically optimal, and local Python wall time is not a production latency claim.
