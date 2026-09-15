# Current state and return contract

## Input universe

| Family | Count | Material |
|---|---:|---|
| LCB kernel/capability | 96 | executable prototype library + V2 registry |
| Foundry parent | 69 | source + tests |
| Foundry product | 145 | source + tests + result/provenance/evidence tier |
| Completed V2 composite | 2 | V2P001 SAVA, V2P002 MFQA |

The base composition registry has 310 records. The two completed composites are packaged products but
have not yet been folded back into that base registry, so the current handoff contains 312 addressable
artifacts. Preserve this distinction.

## Verified checkpoints

- Foundry completion: 214 test files / 806 tests / 0 failures.
- Core V2 semantics: 5/5 tests.
- Foundry-inclusive V2 integration: 5/5 tests.
- V2P001 SAVA: 6/6 tests.
- V2P002 MFQA: 6/6 tests.

These are software/mechanism checkpoints, not general deployment certificates.

## Independent-lab output namespace

Use `V2X001`, `V2X002`, ... for independent products. For each, return:

- complete source and tests;
- parent IDs and exact source paths;
- benchmark inputs/results and comparator;
- strengths, weaknesses, working/failure regions;
- standalone/component roles;
- evidence-vector assessment;
- open risks and next experiment;
- append-only `V2X_REGISTRY.jsonl` and composition edges;
- a new handoff ZIP containing the full independent-lab transcript and chronological method changes.

## Merge rule

The main lab will decide whether to adopt, revise, route or leave each V2X product external. Passing tests
does not force adoption; losing one shell does not force deletion. Preserve all results so they can
supplement later synthesis.
