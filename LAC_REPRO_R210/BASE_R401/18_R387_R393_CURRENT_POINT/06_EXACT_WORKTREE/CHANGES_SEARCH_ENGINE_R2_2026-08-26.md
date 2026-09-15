# LabAllCompass V2 — Search Engine R2 changes

Date: 2026-08-26

R2 replaces the first flat search integration with a representation-corrected, two-stage search architecture. No donor implementation is imported or required.

## Main corrections

1. **Rich corpus restoration.** The first version flattened 310 capabilities into sparse profile text. R2 joins back LCB docstrings, working/failure regions, queue relations, Foundry evidence/strength/weakness text and parent README/interface summaries. 266/310 capability records currently have an additional rich-text source.
2. **Direct retrieval separated from interaction expansion.** The interaction graph cannot inflate first-stage relevance. It is consulted only after a direct capability hit.
3. **Directional interaction semantics.** Known composition edges are traversed as upstream suppliers and downstream consumers. Fuzzy supplier search is fallback-only when a retrieved node has no known edge.
4. **Identity seeds.** Graph expansion uses `doc:<capability_id>` dependencies rather than concatenating a consumer's whole description into a query.
5. **Lexical representation repair.** CamelCase/snake-case splitting, morphology roots, fixed document-length normalization and name-match bonuses were added without breaking linear score-movement certificates.
6. **Persistent session state.** JSON snapshots are fingerprinted against scorer/corpus/graph state and fail closed on mismatch; the CLI supports cross-process reuse.
7. **Search-to-Foundry bridge.** `search_to_foundry.py` now emits direct capabilities, diverse primitive donors, known interaction expansions, fallback hypotheses and score explanations from any problem contract.

## Verification

- focused regression: 24/24 PASS
- 60-edit two-surface incremental replay: 0 top-k mismatches
- naive exact evaluations: 262,910
- R2 exact evaluations: 7,299
- reduction: 97.2238%
- Crypto anchor smoke: all 5 declared capability anchors recovered inside top 20, including K011 at rank 16

Artifacts:

- `01_V2_CORE/generated_search/LAB_SEARCH_ENGINE_BENCHMARK_R2.json`
- `01_V2_CORE/generated_search/SEARCH_RELEVANCE_SMOKE_R2.json`
- `01_V2_CORE/generated_search/CRYPTO_V1_FOUNDRY_SEARCH_PACKET_R2.json`
