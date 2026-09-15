# V2P016_BVRP — Boundary-Viability Reach Planner

Composition: `FOUNDRY:P079 -> LCB-K091`.

Mechanism: CBIA determines whether uncertainty spans opposing reach/avoid actions. The reach-avoid planner uses the nominal action only when the calibrated interval is action-invariant; otherwise it routes to the declared safe fallback.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
