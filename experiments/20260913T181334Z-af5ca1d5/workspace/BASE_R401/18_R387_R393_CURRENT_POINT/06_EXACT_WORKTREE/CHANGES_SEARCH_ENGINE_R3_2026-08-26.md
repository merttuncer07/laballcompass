# Search Engine R3 changes — 2026-08-26

R3 turns R2 retrieval into a controlled learning loop without allowing evaluation leakage into the search that selected a candidate.

## Added

1. `relevance_learning.py`
   - append-oriented feedback ledger;
   - explicit `selection_generation` and `release_generation`;
   - evidence-use roles `LEARN_AFTER_GENERATION`, `PROTECTED_VALIDATION`, `DIAGNOSTIC_ONLY`;
   - exact-shell learning plus attenuated explicitly tagged cross-shell transfer;
   - bounded/shrunk direct, family, and consumer-specific supplier priors;
   - immutable relevance snapshots with fingerprints.

2. Search integration
   - `CertifiedIncrementalSearch` accepts frozen score offsets;
   - offsets participate in the engine fingerprint;
   - changing the relevance snapshot invalidates cached incremental state and fails closed to full search;
   - score explanations expose the learned relevance prior separately from static evidence/component prior and query-feature contributions.

3. Foundry bridge integration
   - search packets carry `search_generation` and `relevance_snapshot_fingerprint`;
   - optional relevance snapshot is used during direct capability/primitive retrieval and consumer-specific supplier expansion;
   - relevance learning remains explicitly separate from promotion/evidence semantics.

4. Operational tooling
   - `record_search_feedback.py` appends a validated event but cannot mutate a live snapshot;
   - `compile_relevance_snapshot.py` freezes the next-generation prior;
   - active `FEEDBACK_LEDGER.jsonl` starts empty.

## Legacy migration decision

No historical benchmark/result was automatically imported as a training event. Audit found:

- 310 capability records;
- 145 Foundry evidence-inventory rows;
- 33 `BENCHMARK_RESULT.json` files in this package;
- zero capability/evidence rows declaring the required `selection_generation`, `release_generation`, and `feedback_role` fields.

Therefore automatic conversion would invent leakage semantics. Legacy artifacts remain evidence/provenance until individually migrated under an explicit role and generation contract.

## Real-corpus mechanics replay

On the 4,310-document corpus and the frozen Crypto V1 problem contract:

- same-generation K069 feedback: quarantined;
- protected-validation K071 feedback: quarantined permanently;
- unrelated-shell P137 outcome: excluded from transfer;
- with only those events, top-30 is exactly identical to the no-learning baseline;
- an explicitly admitted prior-generation K011 development-pass event yields a bounded +0.533333 relevance prior and moves K011 from rank 16 to rank 12.

The K011 movement is a mechanics demonstration using already-known development evidence. It is **not** independent proof that relevance learning improves external discovery quality.

## Verification

Focused Core/Foundry/search/relevance suite: 32/32 PASS.
