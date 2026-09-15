# P097_BDSD — Blackwell-Deduplicated Safeguard Design

**Composition:** CDA + CSID

Uses CDA to certify that a secondary experiment is a garbling/equivalent, then prevents CSID from counting the two safeguards as independent evidence.

## Benchmark

CDA relation `FIRST_STRICTLY_MORE_INFORMATIVE`. Optimistic design selects ['strong_channel', 'garbled_channel']; Blackwell-deduplicated design selects ['strong_channel', 'independent_channel'], avoiding independent-evidence double counting.

## Claim boundary

Blackwell dominance establishes information redundancy, not identical operational failure modes; the shared evidence-family mapping is a declared design policy.

## Verification

6/6 product tests passed.
