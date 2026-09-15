# V2P053 SWCAPL — Support-Weighted Constraint-Aware Policy Learner

**Shadow candidate. Not canonical.**

Composition: `P090 SWDL -> R041 CAPL`.

P090's documented OWS + target-weighted decision-loss mechanism is inserted into CAPL at the optimization objective: caller-supplied target importance weights reweight the realized net-return/risk objective used to learn CAPL's constrained actions. The mechanism-removal control is the same CAPL-style optimizer on the same rows and seed with uniform observation weights.

This is not V2P049 SACAPL (covariance/risk geometry), V2P052 REICAPL (heterogeneous feasible caps), or P090 itself (target-weighted predictive-model selection). It learns a constrained policy under target-weighted direct action performance.

Claim boundary: importance weights must be externally justified. OWS ESS only diagnoses support concentration; it does not establish transportability, causal validity, or real-market performance. A source-like target while using target-shift weights is an explicit failure region.
