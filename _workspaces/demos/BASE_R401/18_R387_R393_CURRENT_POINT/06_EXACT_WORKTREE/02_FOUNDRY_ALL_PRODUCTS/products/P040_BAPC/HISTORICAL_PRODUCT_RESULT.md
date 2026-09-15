# P040 BAPC v0.1 — Blackwell-Audited Persuasion Channel

## Capability

BAPC converts BPISD's optimized binary persuasion policy into an explicit state-by-signal channel and audits it with CDA. It therefore separates sender-optimal information design from utility-independent Blackwell informativeness and from receiver decision value.

## Benchmark result

With prior state-one probability 0.3, the sender prefers adoption while the receiver adopts only when sufficiently optimistic. BPISD finds a Bayes-plausible persuasion experiment with sender gain above **0.49** versus no information. CDA independently certifies:

- full revelation is strictly more informative than the persuasion channel;
- the persuasion channel is strictly more informative than no information;
- receiver decision value respects that information order.

Thus sender value improvement is not mislabeled as maximal informativeness.

## Claim boundary

Blackwell ordering is a property of the channel, not of sender preferences. BAPC does not infer sender welfare from information dominance. BPISD still supplies the persuasion objective; CDA supplies only channel ordering and receiver decision value for the declared utility table.

## Verification

6/6 product tests pass.
