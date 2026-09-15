# P033 CATF v0.1 — Consequence-Aware Time-Frequency Allocation

## Capability

CATF connects TFLD's measured time/frequency localization frontier to ACRA's consequence-weighted resolution allocator. Rather than forcing one analysis window onto every downstream decision region, it assigns a different measured window to each region under a shared acquisition/compute budget.

The adapter is explicit: TFLD time spread and frequency spread are normalized by declared reference scales; sample count is converted to budget units through a declared `cost_per_sample`.

## Benchmark result

At 1 kHz with Hann windows of 16/32/64/128/256 samples, the benchmark contains one time-critical region and one frequency-critical region. Under total budget 10, the best feasible single-window policy uses 64 samples for both regions and has decision-weighted localization loss **17.9939**.

CATF assigns **32 samples** to the fast-event region and **128 samples** to the spectral-fault region. Total cost remains 10 and loss falls to **10.6438**, a **40.85% reduction** versus the best fixed-window policy under the same budget.

## Claim boundary

CATF does not invent a natural exchange rate between seconds, hertz, samples, and operational consequence. The normalization scales, consequence weights, and sample cost are declared inputs. The reported gain is conditional on those declared operational weights.

## Verification

6/6 product tests pass.
