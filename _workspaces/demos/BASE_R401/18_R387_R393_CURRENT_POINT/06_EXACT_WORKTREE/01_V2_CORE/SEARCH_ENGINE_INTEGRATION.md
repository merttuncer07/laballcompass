# Core V2 — Search Engine R2

## Mechanism interpretation

The donor mechanism was not transplanted. Its useful invariant was abstracted:

`SMALL CHANGE -> TRACE WHAT CAN MOVE -> BOUND HOW FAR IT CAN MOVE -> ASK WHETHER THE RETRIEVAL FRONTIER CAN CHANGE -> REUSE OR SELECTIVELY RESCORE`

For LabAllCompass the protected decision is the ordered top-k search result. The engine caches exact scores, accumulates exact movement bounds for this transparent linear scorer, and rescans only the competitive frontier when a query edit could alter membership or order.

## R2 architecture

Search is deliberately two-stage.

### Stage 1 — direct relevance

Capability retrieval and primitive discovery do **not** use graph propagation. A document must earn relevance from the research problem itself. This prevents generic graph hubs or highly connected Foundry parents from becoming universal answers.

The corpus contains:

- 310 executable/product capability records;
- 4,000 canonical primitive records;
- richer mechanism text joined back from LCB docstrings, working/failure regions, queue relations, Foundry strengths/weaknesses/evidence, and parent README/interface summaries when available.

The lexical representation uses:

- exact terms and phrases;
- low-weight five-character morphology roots;
- CamelCase/snake-case decomposition;
- fixed BM25-like document-length normalization;
- transparent name-match bonuses;
- structured strength/input/output/domain features;
- a weak evidence/component prior that cannot dominate problem relevance by itself.

All coefficients are fixed for a corpus, so query-score movement remains exactly bounded.

### Stage 2 — interaction expansion

Only after a direct capability has been retrieved does the engine consult the Lab interaction map.

Known composition edges are traversed exactly in both directions:

- `UPSTREAM_SUPPLIER`: what can repair/support this capability?
- `DOWNSTREAM_CONSUMER`: what can this capability help?

If a direct hit has no known edge, identity-seeded supplier search is allowed as an explicitly labeled hypothesis. The seed is the capability ID itself, not its entire prose description, so graph propagation follows the intended node rather than generic words.

## Search-to-Foundry bridge

`search_to_foundry.py` converts a research problem contract into a machine-readable Foundry packet containing:

1. direct capability candidates;
2. primitive donors, with source-domain diversity preferred but never allowed to shrink the requested frontier;
3. exact known interaction-map expansions around the highest-ranked direct capabilities;
4. hypothetical upstream complements only when a seed has no known interaction edge;
5. per-hit score explanations.

The packet is a search/frontier artifact. It is not promotion evidence and does not modify product validity.

Supported Core V2 entry points:

- `build_catalog_search_engine()` — combined low-level certified search engine;
- `build_search_router()` — separated capability / primitive / supplier surfaces;
- `build_foundry_search_packet(problem_contract)` — direct bridge into Foundry exploration.

CLI:

- `python search_lab.py --mode capabilities --query problem.json`
- `python search_lab.py --mode primitives --query problem.json`
- `python search_lab.py --mode suppliers --consumer-id <ID> --query problem.json`
- `python search_to_foundry.py --query problem.json --output packet.json`

## Correctness verification

R2 focused regression: **24/24 PASS**.

The incremental replay runs 60 deterministic query edits across the actual two search surfaces (310 capabilities + 4,000 primitives). Every incremental top-k is compared with a full exact execution of the same scorer.

- top-k mismatches: **0**
- naive exact score evaluations: **262,910**
- R2 exact score evaluations including initialization: **7,299**
- exact score-evaluation reduction: **97.2238%**
- capability-surface reduction: **91.5706%**
- primitive-surface reduction: **97.6619%**

This is a compute-equivalence result for the declared search scorer. It is not a production latency claim.

## Relevance smoke test

The frozen Crypto V1 problem contract explicitly calls for memory-policy holdout, guarantee transport, selection-aware reference law, memory/lag closure and predictable-variance mechanisms. Direct R2 capability retrieval places:

- `FOUNDRY:P137` MPHA — rank 1
- `LCB-K071` GuaranteeTransportGate — rank 3
- `LCB-K089` SelectionAwareReferenceLaw — rank 9
- `LCB-K011` MemoryKernelClosure — rank 16
- `LCB-K069` PredictableVarianceAlarm — rank 17

All five are inside the top 20. Primitive retrieval independently places Regime transportability rank 2, Drift detector rank 6, Fractional diffusion rank 7, and Treatment-effect decision boundary rank 11.

This is a case-specific smoke test against mechanisms explicitly named by that frozen problem contract, not a general relevance benchmark.

## Non-claims

- Search equivalence does not prove scientific relevance quality.
- Interaction edges are exploration structure, not causal proof.
- A retrieved mechanism is not promoted merely because it ranks highly.
- Hypothetical graph complements require the normal Lab adapter, contrastive benchmark and shell-local validation path.

## Persistent search sessions

`CertifiedIncrementalSearch` and `LabSearchRouter` expose JSON-safe snapshots. The snapshot carries a fingerprint of the scorer version, corpus, eligible set, safety margin and interaction graph. Restore succeeds only on an exact fingerprint match; otherwise the engine remains fresh and the next update performs a full search.

`search_lab.py` accepts `--state-in` and `--state-out`. In a two-process smoke test, the first capability query scored all 310 documents; a modified second query restored the prior state successfully and exactly rescored 21/310 documents while preserving the same top result as full execution. See `generated_search/SEARCH_SESSION_PERSISTENCE_SMOKE_R2.json`.
