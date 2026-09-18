# Q195 Conventions (Steps 3-4)

Extracted from the Q193/Q194 source file and S1. Every formula below is either
a verbatim source statement (with line citation) or is explicitly marked
RECONSTRUCTION. Nothing here is redesigned.

Source files:
- Q193/Q194: `AI_NATIVE_MATH_Q193_Q194_INTERVAL_CODE_SOURCE.md` (339 lines)
- S1: `AI_NATIVE_MATH_MASTER_HANDOFF_2026-09-08.md` (2389 lines)

## Surface chronology

Old F-surfaces chronologically (Q193, lines 3-7):

f_0 < f_1 < ... < f_{H-1}.

Exact ordering (Q193, lines 9-19):

P = (d-1, 1) < f_0, and f_{H-1} = (0, L-1).

Therefore ordered F* (Q193, lines 21-27):

P, f_0, f_1, ..., f_{H-2}.

## Common interval code

Centered interval generator (Q193, lines 29-33): Gamma[a, b].
No explicit edge-sum formula for Gamma is given in the source.

Old code (Q193, lines 35-45):

W_F = span{Gamma[f_0,f_1], ..., Gamma[f_{H-2},f_{H-1}]}.

Current code (Q193, lines 47-58):

W_* = span{Gamma[P,f_0], Gamma[f_0,f_1], ..., Gamma[f_{H-3},f_{H-2}]}.

Common interior (Q193, lines 60-72):

C = span{Gamma[f_0,f_1], ..., Gamma[f_{H-3},f_{H-2}]}.

## Boundary generators

(Q193, lines 74-82):

b_in = Gamma[P, f_0], b_out = Gamma[f_{H-2}, f_{H-1}].

Surface spaces (Q193, lines 84-92):

W_* = C + <b_in>, W_F = C + <b_out>.

For L=3 (Q193, lines 96-104):

b_in = Gamma[h_{d-1}, q_{d-1}], b_out = Gamma[h_0, q_0].

Defect quotient (Q193, lines 106-128): if bulk transversality holds, the
affine/reference closure reduces to the 2D defect D_xi = V_+/(I+J_xi)C,
spanned by [(I+J)b_in] and [P(u)P(v)]. (This is Q196 territory, not Q195.)

## S1 shifted-head lineage (12.1)

(S1, lines 1235-1267.) For L=3, r = 3d, d = 2e+1:

h_a = R_{r-2-2a}, q_a = R_{r-1-2a}.

Inserted: P = R_d = h_{d-1}.

Selected early tail: P, q_{d-1}, q_{d-2}, ..., q_{e+1}; the first q_{d-1}
is a boundary launch.

## S1 F* surgery (section 11)

(S1, lines 1137-1149.):

F* = (F minus {(0,2p)}) union {(d-1,1)}.

## Recurrence normalization

(Q194 section 15.1, lines 136-170.)

Recurrence: R_{k+1} = 1 + x^{s_k} R_k.

Cumulative exponent: P_0 = 0, P_{k+1} = P_k + s_k.

Normalize: S_k = x^{-P_k} R_k.

Then: S_{k+1} = S_k + x^{-P_{k+1}}, and S_k = sum_{i=0}^{k} x^{-P_i}.

REQUIRED INITIALIZATION: the source excerpt does not display R_0. The
executable rig sets R_0 = 1. The R212 audit flags this as a required stated
assumption (R212_STATE.md finding 2). Recorded, not resolved.

## Suffix polynomial

(Q194, lines 172-189.)

Old affine suffix polynomial Q_{k+1} = x^{s_k-1} R_k becomes:

Q_{k+1} = sum_{i=0}^{k} x^{P_{k+1}-P_i-1}.

Each affine row is a directed phase-difference histogram from the current
endpoint to prior prefix states.

## Formal directed edges

(Q194 section 15.2, lines 191-217.)

For every prefix pair i<j, formal edge [i -> j].

Physical projection:

pi([i -> j]) = x^{P_j-P_i-1}

with anti-periodic sign included in projection.

Formal suffix row: tildeQ_j = sum_{i<j} [i -> j].

## Reflection/reversal

(Q194, lines 219-233.)

Reflection is weighted edge reversal: J_xi[i -> j] ~ [j -> i],
with exact intertwining pi J_xi = J_xi pi.

## Forward/reverse codes

(Q194 section 15.3, lines 235-249.)

Lift common interval code to C̃→. Reflected: C̃<- = J_xi C̃→.
Boundary peeling is exact at formal edge level.

## The two distinct statements (never merged)

Formal transversality (Q194, lines 251-264):

C̃→ ∩ C̃<- = 0.

Physical target, the true bulk theorem (Q194 section 15.4, lines 267-287):

ker pi_xi ∩ (C̃→ + C̃<-) = {0}.

The source stresses: one-sided suffix injectivity is not enough; forward
injective + reverse injective does not imply transversality; the theorem is
genuinely two-sided.

## L=3 helical representation (15.5)

(Q194, lines 298-335.) Phase differences admit a one-to-one helical label
(Delta a, Delta t) with Delta a in Z_d, Delta t in Z_3, because
gcd(n_0,3)=1. pi is a signed histogram over helical displacement classes.
The canonical word's horizontal residue follows the mountain
0 -> 1 -> ... -> d-1 through recipient +1 steps, then plateaus with donor
-1 events d-1 -> ... -> 0. Bulk theorem restated: no nonzero forward/reverse
coefficient packet on the canonical 3-layer mountain has zero signed weight
in every helical bin.

## What the source does NOT define (RECONSTRUCTION notice)

The source never writes Gamma[a,b] as an explicit edge sum. The chat
identification Gamma[a,b] = tildeQ_b - tildeQ_a (directed suffix difference,
pi(Gamma) = Q_b - Q_a) is a UNIONALLPHA RECONSTRUCTION consistent with the
15.1 telescoping identity, not a source definition. The recovered harness
uses it and every reconstructed section is marked accordingly.

# HISTORICAL STUB WARNING

The frozen file `q195_suffix_lift.py` (SHA-256
82f8b1a036668cba641bb97659f937d3e0af0ac17c680314f24649090f2b81e1)
contains, lines 101-112:

```python
def helical_label(exp, d, n):
    """Map a phase difference exp = P_j - P_i to (Delta a, Delta t).

    The word's horizontal cumulative residue follows the mountain:
    label = (horizontal displacement in Z_d, vertical in Z_3) recovered from
    exp = (n + g)-drift decomposition. For the L=3, n0=1 word the physical
    phase difference P_j - P_i decomposes as n0*(Delta t)*d + Delta a*(n+1)
    ... the exact bijection: exp = Delta_a*(n0*d) + Delta_t*d? Determined by
    the generator structure; we use the report's identification
    exp = (n+1)*j_a + n*j_t (successor-splice composition).
    """
    raise NotImplementedError
```

Comparison against the later working UnionAlpha chat derivation (transcript
Block 16: gap-value decomposition g_k = s_k - n with
1 -> (1,0); 0 -> (0,1); r-1 -> (-1,1); r or 2r -> (0,2)):

Verdict: INCONSISTENT.

The stub's docstring formula (exp = (n+1)*j_a + n*j_t) matches neither the
source 15.5 statement (pair determines class via gcd(n_0,3)=1, no explicit
formula given) nor the chat's gap-decomposition map, and the body raises.

DO NOT USE THE OLD helical_label() STUB AS THE Q195 CONVENTION.
The old file is historical evidence and remains unedited.
