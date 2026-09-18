# Q196 Quadratic Telescoping (§8, polynomial identity)

For Q_k^ξ(x) = R_k(x)·R_k(ξ/x) in K[x]/(x^r+1) and any interval [a,b]:

Q_b^ξ − ξ^{P_b−P_a} Q_a^ξ = (I+J_ξ)Γ[a,b].

Verified as an exact polynomial identity (mod x^r+1) for every C
interval plus both boundary intervals, at every V4 cell (both primes,
all ξ). Proof sketch from the transition identity: the scalar identity
Q_{k+1} − ξ^{s_k}Q_k = R_{k+1}(u) + R_{k+1}(v) − 1 with v = ξ/u lifts to
polynomials because J_ξ acts as (Jf)(x) = f(ξ/x) and the centered
subtraction absorbs the constant; scaling by ξ^{P_b−P_h} telescopes.
The machine check is the normative verification here.

## Propagation (§§9-10, verified consequences)

With q_k = λ⋆(Q_k^ξ): annihilation of C-intervals gives
q_b = ξ^{P_b−P_a} q_a (checked per cell); hence
q_{r−2} = ξ^{P_{r−2}−P_d} Θ. The outgoing interval gives
q_{r−1} − ξ^{s_{r−2}} q_{r−2} = 2 (checked), i.e.
Θ = ξ^{−(P_{r−1}−P_d)}(q_{r−1} − 2). General Q196 is now the single
scalar q_{r−1} = λ⋆(R_{r−1} J_ξ R_{r−1}).
