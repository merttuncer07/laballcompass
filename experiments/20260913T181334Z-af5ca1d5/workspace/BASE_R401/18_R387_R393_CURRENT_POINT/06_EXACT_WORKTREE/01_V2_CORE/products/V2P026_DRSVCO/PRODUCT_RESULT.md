# V2P026_DRSVCO — Decision-Relevant Stateful Cycle Explorer

Composition: `PARENT:IM334_IM094_DRE -> FOUNDRY:P035`.

Mechanism: DRE allocates the next stateful-cycle evaluation to the operating point whose uncertainty can most plausibly change the feasible SVCO winner, instead of evaluating the statically highest-throughput point by default.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
