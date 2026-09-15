# LabAllCompass R3 — Search relevance feedback contract

## Purpose

Search outcomes may teach **future retrieval order**. They do not change scientific evidence tiers, product promotion state, or benchmark claims.

The feedback loop is:

`FROZEN SEARCH GENERATION -> RETRIEVE / COMPOSE -> EVALUATE -> APPEND TYPED OUTCOME -> CLOSE GENERATION -> COMPILE NEXT FROZEN RELEVANCE SNAPSHOT`

There is no direct path from an evaluation result back into the live search weights that selected it.

## Required event fields

- `event_id`: globally unique feedback event id.
- `subject_id`: capability/mechanism document id receiving the outcome.
- `selection_generation`: search generation that selected the subject.
- `release_generation`: generation in which the outcome became available.
- `problem_shell`: explicit shell in which the outcome was observed.
- `shell_tags`: optional controlled transfer tags.
- `outcome`: `HELPED`, `HURT`, `NEUTRAL`, or `INCONCLUSIVE`.
- `weight`: predeclared confidence/relevance weight in `[0,1]`; it is not a p-value.
- `role`: one of the evidence-use roles below.
- `consumer_id`: optional. When present, the result teaches only supplier relevance for that consumer and is not promoted to a global capability prior.
- `provenance`: source artifact/test/result identifiers.

## Evidence-use roles

### `LEARN_AFTER_GENERATION`
May affect a later search generation only when both `selection_generation < target_generation` and `release_generation < target_generation`.

### `PROTECTED_VALIDATION`
Never trains search relevance. Use for untouched/final/external validation that must remain an audit surface rather than become retrieval training data.

### `DIAGNOSTIC_ONLY`
Never trains search relevance. Use for debugging, implementation checks, or observations that should remain visible without influencing retrieval.

## Shell transfer

An exact `problem_shell` match gets full relevance-learning weight. Cross-shell transfer occurs only when both sides declare shared `shell_tags`, and is deliberately attenuated. No shared tag means zero transfer.

## Bounded priors

Learning is a weak retrieval prior, not a replacement for mechanism relevance:

- direct per-capability bonus is shrinkage-limited and capped;
- family-level transfer is weaker and requires outcomes from at least two distinct members of the family;
- supplier/consumer feedback is consumer-specific;
- historical success cannot make a document match query features it does not possess.

## Incremental-search safety

A relevance snapshot is immutable within one search generation and participates in the search-engine fingerprint. Changing the snapshot changes the fingerprint. A cached incremental-search state created under another relevance snapshot therefore fails closed and triggers full search.

## Legacy evidence

Existing Lab benchmark/result files are **not automatically imported** into the learning ledger. Most predate this contract and do not declare selection generation, release generation, or evidence-use role. They remain evidence and provenance until explicitly migrated under a justified mapping.
