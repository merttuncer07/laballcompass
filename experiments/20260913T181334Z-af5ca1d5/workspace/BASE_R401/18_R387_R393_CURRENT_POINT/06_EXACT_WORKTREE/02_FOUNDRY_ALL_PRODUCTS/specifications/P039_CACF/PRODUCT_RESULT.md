# P039 CACF v0.1 — Control-Aware Circular Flow

## Capability

CACF overlays HFAD transaction-flow topology with OWNM ownership/control propagation. HFAD separates potential flow from local-cycle and harmonic circulation; OWNM marks companies controlled by a declared investor while separately reporting ultimate cash exposure. CACF measures how much circulation lies wholly inside that controlled company set.

## Benchmark result

A three-company transaction triangle carries equal `10,10,10` round-trip flows. HFAD decomposes this as **pure local-cycle flow**: local-cycle energy 300, potential energy 0, circulation fraction 1. The same companies form a 51%-51% ownership pyramid. Voting control propagates from the investor through A→B→C, so all three endpoints are controlled and **100% of circulation energy** is inside the controlled set.

Economic exposure remains separate: ultimate cash exposure to C is only `0.51^3 = 0.132651`, despite control of C. A tree-flow counterexample has zero circulation and does not flag.

## Claim boundary

The transaction graph and face complex are explicit inputs. The output is a structural screening signal for controlled circular flow, not a legal or factual determination of fraud, money laundering, or intent. Voting control is never substituted for economic ownership.

## Verification

6/6 product tests pass.
