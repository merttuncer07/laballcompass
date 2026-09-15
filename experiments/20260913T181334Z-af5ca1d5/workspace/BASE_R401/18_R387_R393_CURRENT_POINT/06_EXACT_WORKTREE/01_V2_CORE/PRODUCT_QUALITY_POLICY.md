# Product-quality policy — anti-iteration-inflation gate

A completed executable edge is not automatically counted as a distinct product family.

A candidate may be counted as `DISTINCT_PRODUCT` only when all of the following are explicit:

1. **New failure mode** — a concrete error that the existing product set does not already close in the same way.
2. **Non-additive interaction** — one mechanism changes the feasible set, objective, state update, uncertainty geometry, target, or evidence validity of the other. A cosmetic pre-gate, renamed threshold, or `filter -> max()` wrapper is insufficient by itself.
3. **Nearest-product comparison** — name the closest existing product and state the mechanistic difference.
4. **Mechanism-removing control** — run the same declared shell with the new mechanism removed wherever an executable control is possible.
5. **Boundary / abstention** — invalid support, missing certificate, unsafe region, or unidentifiable state must fail closed rather than silently produce a decision.
6. **Executable contract** — invariant tests and a deterministic mechanism benchmark are required before telemetry closure.
7. **Evidence honesty** — synthetic mechanism evidence is not empirical, transfer, operational, or deployment evidence.
8. **Family accounting** — multiple adapters that differ mainly by supplier-specific precondition or consumer-specific routing are recorded as executable variants but count as one distinct product family until a deeper benchmark proves a new operator.

Throughput is optimized after this gate, not before it.
