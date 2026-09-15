# P035 SVCO v0.1 — Stateful Volcano Cycle Optimizer

## Capability

SVCO composes VICO's static opposing-bottleneck operating-point search with SCCRT's finite catalyst-state cycle. Every declared coupling is evaluated under the same reactant, oxidant and regeneration schedule; selection is then restricted to couplings that sustain minimum and final active-lattice requirements.

## Benchmark result

VICO alone selects coupling **3.0** because its static serial throughput is **2.4**, the maximum of the declared volcano surface. Under the identical 100-step catalyst-state cycle, coupling 3 reaches a minimum active fraction of roughly **0.210**, below the required **0.25**. The stateful feasible optimum shifts to coupling **2.0**, whose minimum/final active fraction is about **0.285** while producing more cycle product than the other feasible couplings.

The result is not a generic claim that weaker coupling is preferable. It demonstrates the narrower mechanism: a static volcano optimum can be infeasible once the catalyst's own consumable/restorable state is included.

## Claim boundary

The adapter interprets VICO aggregate throughput as a normalized full-active SCCRT product rate. This is an explicit modeling contract, not a claim that VICO estimates arbitrary kinetic constants. All couplings face the same feed/regeneration schedule; otherwise the comparison would confound operating point with regeneration policy.

## Verification

6/6 product tests pass.
