# Product batch 4 — quality-first distinct mechanisms

This batch changes product accounting as well as adding products.

## Why

The previous accelerated batch increased throughput but over-concentrated on related routing/precondition adapters, especially around DRE. Executable evidence remains valid, but executable-suite count is not equivalent to genuinely distinct product count.

## New quality gate

`01_V2_CORE/PRODUCT_QUALITY_POLICY.md` now requires, for a new distinct product family:

1. a new failure mode;
2. a non-additive mechanism interaction;
3. explicit nearest-product comparison;
4. a mechanism-removing comparator;
5. fail-closed/abstention behavior at the declared boundary;
6. an executable deterministic mechanism benchmark;
7. an explicit evidence/nonclaim boundary;
8. family accounting that collapses shallow adapter variants.

`01_V2_CORE/audit_product_quality.py` checks the mechanical parts of this contract and writes/validates `PRODUCT_QUALITY_AUDIT_V1.json`.

## Retroactive accounting

Before this batch there were 28 executable suites. The quality audit counts them as **18 distinct product families**, collapsing three near-duplicate adapter groups while preserving every suite and telemetry event.

## New distinct products

### V2P029 SUSCA
Support-Adjusted Shared Capacity Allocator. BOSA-style effective support changes marginal ordering inside overlapping shared-capacity allocation; low-support nominal winners can no longer consume scarce shared capacity merely because their point estimate is high.

Mechanism-removing control: the same allocator with support forced to 1. In the declared synthetic shell, realized support-weighted value rises from 55 to 105.

### V2P030 PCFDLW
Predictive-Closure-Fidelity Decision-Loss Workbench. Representation candidates must pass recursive closure/fidelity certification before downstream decision-loss selection; this blocks training-good but recursively invalid compressed states from being selected.

Mechanism-removing control: downstream decision-loss selection without the closure/fidelity gate.

### V2P031 QDRA
Quasineutral Decision-Relevant Resolution Allocator. Current belief mass near a declared validity boundary becomes the consequence weight inside shared discrete resolution allocation, so precision is spent where it can alter a decision rather than where raw consequence alone is large.

Mechanism-removing control: the same allocator using raw consequence weights.

### V2P032 SPITWMR
Search-Policy Information Targeted Model Reduction. Search-policy sensitivity defines the protected output for model reduction, changing which latent state is retained. This is proactive target-driven reduction rather than post-hoc compression auditing.

Mechanism-removing control: energy-based state retention.

### V2P033 VCMF
Viability-Constrained Multi-Fidelity Budget Controller. Fine/cheap measurement mixtures are optimized under a hard worst-case bias bound derived from the current viability margin, preventing cheap high-count plans whose bias can cross the viability boundary.

Mechanism-removing control: variance/cost-only multi-fidelity selection.

### V2P034 SCOPG
Support-Constrained Observation-Policy Guard. A weighted passive-state-adjusted backaction regression emits a policy coefficient only when effective sample size and design geometry support the estimate.

Mechanism-removing control: the same weighted regression without support certification.

### V2P035 ISTAICC
Information-Search Tipping AICC. Immediate acquisition value is augmented by continuation value from the **reachable** search-participation equilibrium from the current state; using the maximum fixed point is explicitly rejected because it erases basin/hysteresis structure.

Mechanism-removing control: immediate net-value acquisition only.

### V2P036 PCFMCSC
Predictive Closure-Fidelity Comparative-Statics Certificate. Instead of assuming one monotone tipping threshold, the mechanism audits the full ordered tolerance grid, returns direction violations, and reports safe intervals.

Mechanism-removing control: the single-threshold assumption that all larger tolerances are unsafe after the first negative margin.

### V2P037 DWPCFT
Decision-Weighted PCFT Calibration Allocator. A finite calibration budget is allocated across closure/fidelity tolerance points by downstream consequence, distance to boundary, and diminishing inverse-square-root uncertainty reduction.

Mechanism-removing control: uniform calibration allocation.

### V2P038 BOSARO
Burnout-Support Admissible-Shift Robust Optimizer. Effective support inflates the directional robust uncertainty radius, changing the robust simplex solution when a nominally attractive action is supported only in a fragile region.

Mechanism-removing control: the same robust optimizer with support fixed to one.

## Verification

- New focused product tests: 82/82 PASS.
- New distinct-product quality gates: 10/10 PASS.
- New telemetry events: 82/82 COMPLETE.
- Canonical telemetry after refresh: 316 events, 316/316 exact current-suite matches, 38/38 completed suites calibrated.
- Interaction map after refresh: 38 completed, 962 inferred, 53 parent, 4 rejected edges.
- Top-level Core/search/telemetry/closure regression: 86/86 PASS.
- Learning-eligible empirical campaign outcomes: 0.

These are deterministic mechanism-shell results. They do not establish scientific validity, market profitability, or real-world performance.
