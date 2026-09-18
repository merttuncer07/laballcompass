# Q195 Exact Interval Derivation (Phase 1)

Status: VERIFIED — proofs below + machine checks (all ξ^r = 1, u ∈ {2,3,5},
two primes per case, d = 3,5 (n0 = 1,2), d = 7 (n0 = 2), d = 9 (n0 = 1)).

## Older-source verdict

`VOLTERRA_ALAN_MASTER_HANDOFF_2026-09-03 (2).md` and `Araştırma Devamı.txt`
do NOT exist locally (home-wide glob: no hits) and occur NOWHERE in stored
chat history (Devam/09-03 hits are unrelated). The derivation below is
verified directly from the stated recurrence; provenance: USER-SPECIFIED,
machine-checked. It is NOT presented as a recovered older text.

## Setup

R_{k+1} = 1 + x^{s_k} R_k, P_0 = 0, P_{k+1} = P_k + s_k, R_0 = 1.
For uv = ξ: Q_k = R_k(u) R_k(v).

## Base identity

Q_{k+1} − ξ^{s_k} Q_k = R_{k+1}(u) + R_{k+1}(v) − 1.

Proof: Q_{k+1} = (1+u^sR_k(u))(1+v^sR_k(v))
= 1 + u^sR_k(u) + v^sR_k(v) + ξ^sQ_k, while
R_{k+1}(u)+R_{k+1}(v)−1 = 1 + u^sR_k(u) + v^sR_k(v). ∎

## Telescoping (a < b, w_h = ξ^{P_b−P_h})

Q_b − ξ^{P_b−P_a} Q_a = Σ_{h=a+1}^{b} w_h [R_h(u) + R_h(v) − 1].

Proof: scale the base identity at step h−1→h by ξ^{P_b−P_h} and sum;
left side telescopes. ∎

## Centered interval polynomial

G_{a,b}(x) = Σ_{h=a+1}^{b} w_h R_h(x); c_{a,b} = Σ w_h;
Γ[a,b](x) = G_{a,b}(x) − c_{a,b}/2 (p odd, 2 invertible).

Then Q_b − ξ^{P_b−P_a} Q_a = Γ[a,b](u) + Γ[a,b](v),
since Γ(u)+Γ(v) = Σw_h(R_h(u)+R_h(v)) − c = Σw_h(R_h(u)+R_h(v)−1). ∎

This identity PASSED machine verification before any further phase.

## Answer to the report question

Is Q193's Γ[a,b] confirmed to be the older Ĝ_{a,b}? The older text is
absent, so textual confirmation is impossible. What IS confirmed: the
centered object above satisfies exactly the splitting
Q_b − ξ^{ΔP}Q_a = Γ(u) + Γ(v) that an interval code needs, and its
suffix-side form (Phase 2) matches the Q194 suffix code term by term.
Status: MATHEMATICALLY VERIFIED reconstruction, not a recovered quotation.
