# IM-421 → IM-094 product result: Decision-Targeted Private Release v0.2

## Working result

The composition now exists as executable software rather than only a proposed connection.

It accepts public decision rules and local private records, derives bounded-query sensitivity,
allocates a finite epsilon budget toward decisions with real operational consequence, adds calibrated
Laplace noise, and releases an action instead of the underlying score. Repeated releases are limited
by a composition accountant and recorded in a hash-chained ledger.

Supported first-version score builders:

- boolean condition counts, sensitivity 1;
- bounded sums under explicit add/remove or replace-one adjacency.

## Construction evaluation

Emergency-dispatch example:

- protected action: dispatch when a private urgent-case count reaches 30;
- total privacy budget: epsilon 1;
- comparison system: a 12-statistic dashboard dividing epsilon equally;
- DTPR system: the action-relevant count receives the available budget and zero-consequence
  descriptive releases are omitted;
- 31 true count levels from 15 through 45;
- 10,000 releases at every level; fixed evaluation seed 20260825;
- false-negative cost 5 and false-positive cost 1.

| Result | Uniform 12-statistic dashboard | DTPR |
|---|---:|---:|
| Epsilon available to dispatch decision | 0.083333 | 1.000000 |
| Laplace scale on dispatch count | 12.0 | 1.0 |
| Action error rate | 0.281123 | 0.035274 |
| Mean operational error cost | 0.876942 | 0.138887 |

DTPR reduced action error by **87.45%** and the declared operational error cost by **84.16%** in this
construction shell. The gain comes from not consuming privacy capacity on outputs that do not alter
the protected action.

## Multi-site resource allocation

The second construction moves beyond binary thresholds. Eight sites have private urgent-case counts
and only two emergency teams are available. The comparison dashboard privately releases all eight
counts by dividing epsilon equally, then selects the two largest. DTPR instead applies two composed
exponential-mechanism selections and releases only the selected sites.

Across 50,000 generated operating situations at the same total epsilon 1:

| Result | Private full-count dashboard | DTPR action-only allocation |
|---|---:|---:|
| Private counts released | 8 | 0 |
| Actions released | 2 | 2 |
| Exact top-two selection | 23.05% | 41.08% |
| Captured priority fraction | 86.12% | 93.61% |
| Mean unserved-priority regret | 6.9713 | 3.2097 |

Decision-only allocation reduced resource-allocation regret by **53.96%** while publishing less
private operational detail.

## What is already usable

- Python library with no third-party dependency;
- multi-threshold actions;
- decision-weighted epsilon allocation;
- cryptographic operating-system randomness in unseeded operation;
- raw/noisy score hidden by default;
- public rule fingerprint in every release;
- local CSV adapter;
- explicit adjacency and derived sensitivity for supported queries;
- lifetime epsilon accounting and tamper-evident JSONL ledger;
- binary and multi-threshold actions;
- action-only argmax and top-k resource allocation through the exponential mechanism;
- nine automated tests, all passing.

## Honest boundary of v0.1

This is a working reference engine, not yet a production privacy service. Production deployment
needs authenticated policy approval, concurrent ledger locking, remote signing or an append-only
store, independent review of each sensitivity declaration, and secure process isolation. These are
the next engineering layers; they do not invalidate the working allocation-and-release mechanism.

## Next product construction

Connect the multi-site selector to the CSV policy adapter, then add authenticated policy approval and
atomic concurrent ledger writes. After that, the main scientific construction question is dynamic
budgeting: reserve epsilon for future decisions when current action gaps are already large, and spend
more only when the private action is genuinely ambiguous.
