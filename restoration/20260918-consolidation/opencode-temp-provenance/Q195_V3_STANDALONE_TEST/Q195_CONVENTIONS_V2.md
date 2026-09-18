# Q195 Conventions V2 (Phase B, source-faithful)

Supersedes the V1 code's surface selection, NOT the V1 provenance record.
Source statements verified in S1/Q193-Q194 files; forced identification
(a,1) = h_a, (a,2) = q_a as instructed.

## Faithful F*

F = {(a,2)} ∪ {(a,1): a<=e}; F* = (F \ {(0,2)}) ∪ {(d-1,1)}.
Under the identification: F* = {q_1..q_{d-1}} ∪ {h_0..h_e} ∪ {h_{d-1}=P}.
|F*| = H = (r+1)/2 = 3e+2. f_0 = q_{d-1}; f_{H-1} = (0,2) = q_0 (outside F*).

## Faithful chronology (B4, machine-checked)

t(h_a) = r-2-2a; t(q_a) = r-1-2a.
d=3: (h_2,q_2,h_1,q_1,h_0), times [3,4,5,6,7].
d=5: (h_4,q_4,q_3,h_2,q_2,h_1,q_1,h_0), times [5,6,8,9,10,11,12,13].

## Faithful common core (B5)

T_0 = P, T_1 = f_0, ..., T_{H-1} = f_{H-2}.
b_in = Γ[T_0,T_1]; C = span{Γ[T_1,T_2]..Γ[T_{H-2},T_{H-1}]} (H-2 = 3e
generators); b_out = Γ[T_{H-1}, q_0] kept as separate object.

## Gamma status (B6, from Phase A)

NEW RECONSTRUCTION. No source edge formula; no prehistory derivation.
Provisional use only: Gamma[a,b] = tildeQ_b - tildeQ_a.

## Reflection status (B7, from Phase A)

EXACT EDGE-REVERSAL WEIGHT NOT RECOVERED. Plain reversal used ONLY for
the B9 provisional diagnostic. No rank result here is Q195.
Intertwining pi J = J pi has NO edge-by-edge unit test because the exact
J_xi is unavailable; constructing one is blocked on the weight.
