# V2P003 MFPD — Multi-Fidelity Persistence Diagnostics

## Composition

LCB `MultiFidelityBudgetControllerV0` + Foundry `P144 DPAI`.

The composition order is strict. P144 first estimates the persistence parameter and asks whether another identification measurement has positive downstream decision value near the stability boundary. K048 is invoked only after that acquisition gate. It then allocates a declared fixed program budget between fine and cheap identification measurements using their costs and a declared pilot cross-fidelity correlation.

This avoids giving the budget controller scientific authority it does not have: K048 cannot decide that persistence evidence is needed; it can only route a budget after P144 says acquisition is decision-relevant.

## Adapter contract

Inputs added to P144's persistence shell:

- `total_budget`;
- fine and cheap identification-channel noise variances and per-measurement costs;
- `pilot_correlation` between the two fidelity measurements;
- `min_fine` and `min_correlation` routing guards.

Outputs preserve P144's persistence estimate, standard error, current action and acquisition/no-acquisition semantics, then add `mode`, `n_fine`, `n_cheap`, `spent_budget`, and a separate K048 variance proxy.

## Evidence surface

The frozen development suite has two parts:

1. six P144 invariant-preservation cases on the composed path;
2. six contrastive composition cases that specifically exercise K048's contribution: high-vs-low correlation routing, cheap-channel negative value, budget preservation, and variance-proxy improvement over the fine-only baseline.

The variance proxy remains a program-design approximation. It is not persistence uncertainty, action loss, or scientific validation.

## Boundary

All channel noise, costs, pilot correlation and budget are declared inputs. The composition does not infer cross-fidelity sensitivity or correlation from DFDPE. Failure should route to recalibration/fine-only/no-acquisition according to the failed contract; it does not delete either base mechanism.
