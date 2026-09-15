# LabCompass Core V2 — capability, product and evidence logic

## Objective

Core V2 searches for mechanisms that can produce useful, working systems. Academic novelty, consensus,
publication fit and patent positioning are metadata. They do not decide whether a capability is worth
building or testing.

The unit of record is no longer “an idea that survives or dies.” It is a **capability with a mapped
operating region**.

## Five layers that must not be collapsed

1. **Mechanism** — the causal/mathematical operator that might create value.
2. **Kernel** — executable implementation of that operator.
3. **Product shell** — data adapter, user decision, workflow, interface and economics.
4. **Router/fallback** — detects whether the qualified region holds and chooses the kernel, a baseline,
   abstention or escalation.
5. **Evidence vector** — separate maturity on code, mechanism, held-out transfer, operational value and
   deployment.

A Python class is not automatically a distinct product or even a distinct kernel. A helper class may
remain a helper. Conversely, a mechanism need not receive a new ontology ID to become a valuable
standalone product shell.

## Revised benchmark logic

The old phrase “destructive benchmark” is replaced by **contrastive boundary benchmark**.

The purpose is not to make an idea fail. The purpose is to learn:

- where it beats a strong relevant baseline;
- where it ties or loses;
- which mechanism explains the difference;
- whether the loss is implementation, calibration, data-shell, use-case or mechanism failure;
- what router or fallback turns the combined system into a reliable product.

Every benchmark record must name:

- data or generator;
- shell/use case;
- comparator and why it is relevant;
- metric tied to the actual decision;
- uncertainty or replication;
- working region and failure region;
- safest next experiment;
- standalone value and component value separately.

## Locality rule for negative evidence

A negative result has the form:

`candidate loses/ties comparator C on metric M in shell S using data D`.

It is never silently generalized to “the product is dead.” The default response is one of:

- narrow the working region;
- add a router/fallback;
- redesign the shell;
- repair the implementation;
- keep it as a component;
- mark the result inconclusive and collect better data.

Only a proven logical contradiction can invalidate a precisely stated mechanism claim. Even then, the
implementation and neighboring product shells remain separate records.

## Evidence vector

Evidence is not one scalar score.

| Axis | Question |
|---|---|
| Code | Does the implementation satisfy its invariants and independent tests? |
| Mechanism | Does it beat a mechanism-removing control or strong comparator in a declared shell? |
| Transfer | Does the effect carry to held-out or domain-native data? |
| Operational value | Does it improve a real decision after realistic costs and constraints? |
| Deployment | Does it remain calibrated across domains/regimes with monitoring and fallback? |

Commercial upside and evidence maturity are reported separately. A high-value PP1 candidate is not
called production-ready; a PP3 product is not automatically the most valuable product.

## Product-role rule

Each capability receives two independent evaluations:

- **standalone product:** can a user obtain a complete decision or workflow outcome from it?
- **component:** does it materially improve another product, protect it, calibrate it or route it?

“Merge into existing core” means an interface relationship, not deletion. The child capability,
benchmark, working region and provenance remain addressable.

## Domain selection and safety

Early real-world tests should prefer recoverable, observable, low-harm settings. A domain where every
possible intervention is attempted because people may die is often a bad first discriminator: it can
hide selectivity, distort baselines and make failure ethically expensive. The initial use case is a
measurement instrument, not the final market boundary.

## Core V2 lifecycle

1. Preserve provenance and reconstruct the mechanism precisely.
2. Build or recover an executable kernel.
3. Run invariant and oracle tests.
4. Run a contrastive boundary benchmark with a strong baseline.
5. Map working and failure regions.
6. Test standalone and component value separately.
7. Add router, fallback and abstention behavior.
8. Move to held-out/domain-native data.
9. Run operational pilots with real costs and constraints.
10. Expand across regimes/domains; only then claim production maturity.

## What is retained from the supplied project

- value-first prioritization;
- explicit provenance;
- strong comparators and mechanism-removing controls;
- preservation of failed and corrected runs;
- separation of focused tests from real-world validation;
- distinction between commercial rank and proof rank;
- shell-specific gates, invariance and symmetry controls;
- no academic-novelty veto.

## What is changed

- “survives/does not survive” becomes working-region evidence;
- arbitrary promotion thresholds no longer erase a positive mechanism effect;
- class count is not reported as product count;
- merges preserve the child capability and its evidence;
- real-world loss triggers diagnosis and routing, not global product death;
- production readiness requires all evidence axes, not a high synthetic benchmark score;
- the strongest comparator from any valid replication is retained even if a later file omits it.

## Foundry integration extension

Foundry is now a first-class capability family beside LCB kernels and the 69 parent products. Its 145
product IDs enter with their actual evidence tier; they do not receive a common promotion label.

- original executable material;
- salvaged source with rebuilt tests;
- mechanism reconstructed from preserved results;
- spec-executable reconstruction from results;
- new replacement for a completely unrecoverable historical ID.

Strength/weakness matching is a candidate generator, not an automatic composition theorem. Automated
edges are reranked by interface type, evidence level, non-additive mechanism fit, standalone value and
component value. Curated judgment is recorded explicitly rather than hidden inside a scalar score.

The first completed route is `LCB SharedCapacityAllocatorV0 → Foundry P031 EVLT → V2P001 SAVA`.
It replaces additive audit-value arithmetic with posterior scenario re-optimization under overlapping
capacity pools. Exact subset search remains available for small portfolios; large portfolios route to
a scalable polymatroid allocation and retain that relaxation label.

The second completed route is `LCB MultiFidelityBudgetControllerV0 → Foundry P136 QAIG → V2P002 MFQA`.
It separates two questions that ordinary budget allocation conflates: whether another measurement can
materially alter the declared validity decision, and—only after that gate opens—whether a cheap proxy is
correlated enough with the fine channel to deserve budget. The output preserves QAIG decision value and
the LCB variance proxy as different quantities. Low-correlation cases route to fine-only acquisition;
far-from-boundary cases abstain and preserve the budget.


The third completed route is `LCB MultiFidelityBudgetControllerV0 → Foundry P144 DPAI → V2P003 MFPD`.
P144 retains scientific authority over whether persistence information is worth acquiring near the stability boundary.
Only after that gate opens does the K048 mechanism divide a fixed declared budget between fine and cheap identification measurements using declared costs and pilot cross-fidelity correlation. High-correlation development cases may route to a mixed program; low-correlation cases fall back to fine-only; far-from-boundary cases still abstain. The K048 variance proxy remains separate from persistence uncertainty and action loss.

R8 adds `LCB ObservationPolicyConfoundingGuardV0 → Foundry P138 SPIA → V2P004 OPIA`. The adapter does not apply K081's scalar coefficient directly to a probability vector. It requires a declared zero-sum effect contrast, estimates observation-induced scalar backaction after passive-state adjustment, converts it to a minimum-norm simplex-tangent belief shift, and lets P138 recompute channel utility with that physical shift included. Missing channel-specific backaction history fails closed.
