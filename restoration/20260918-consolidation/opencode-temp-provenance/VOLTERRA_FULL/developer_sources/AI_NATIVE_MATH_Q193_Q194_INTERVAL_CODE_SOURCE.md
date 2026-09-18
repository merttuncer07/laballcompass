# 14. Q193 — \(F\to F^*\) IS RANK-ONE SURGERY AT INTERVAL-CODE LEVEL

Let old \(F\)-surfaces be chronologically:

\[
f_0<f_1<\cdots<f_{H-1}.
\]

Exact ordering:

\[
P=(d-1,1)<f_0
\]

and:

\[
f_{H-1}=(0,L-1).
\]

Therefore ordered \(F^*\):

\[
\boxed{
P,f_0,f_1,\ldots,f_{H-2}.
}
\]

Define centered interval generator:

\[
\Gamma[a,b].
\]

Old code:

\[
W_F
=
\operatorname{span}
\{
\Gamma[f_0,f_1],\ldots,
\Gamma[f_{H-2},f_{H-1}]
\}.
\]

Current code:

\[
W_*
=
\operatorname{span}
\{
\Gamma[P,f_0],
\Gamma[f_0,f_1],\ldots,
\Gamma[f_{H-3},f_{H-2}]
\}.
\]

Common interior:

\[
\boxed{
C
=
\operatorname{span}
\{
\Gamma[f_0,f_1],\ldots,
\Gamma[f_{H-3},f_{H-2}]
\}.
}
\]

Boundary generators:

\[
b_{\rm in}=\Gamma[P,f_0],
\]

\[
b_{\rm out}=\Gamma[f_{H-2},f_{H-1}].
\]

Then exactly:

\[
\boxed{
W_*=C+\langle b_{\rm in}\rangle,
\qquad
W_F=C+\langle b_{\rm out}\rangle.
}
\]

Thus the surface-level one-orbit exchange is also a **one-generator interval-code surgery**.

For \(L=3\):

\[
b_{\rm in}=\Gamma[h_{d-1},q_{d-1}],
\]

\[
b_{\rm out}=\Gamma[h_0,q_0].
\]

If common-core reflection transversality holds, then the whole affine/reference closure reduces to a 2-dimensional defect quotient:

\[
\mathfrak D_\xi
=
V_+/(I+J_\xi)C.
\]

Only:

\[
[(I+J)b_{\rm in}]
\]

and:

\[
[P(u)P(v)]
\]

need span that 2D defect.

This is a constant boundary closure, conditional on the bulk lemma.

---

# 15. Q194 — SUFFIX-INCIDENCE LIFT AND THE TRUE BULK COLLISION LEMMA

This is the latest completed derivation.

## 15.1 Exact suffix normalization

Recurrence:

\[
R_{k+1}=1+x^{s_k}R_k.
\]

Cumulative exponent:

\[
P_0=0,\qquad P_{k+1}=P_k+s_k.
\]

Normalize:

\[
S_k=x^{-P_k}R_k.
\]

Then:

\[
\boxed{
S_{k+1}=S_k+x^{-P_{k+1}}
}
\]

and:

\[
\boxed{
S_k=\sum_{i=0}^{k}x^{-P_i}.
}
\]

Old affine suffix polynomial:

\[
Q_{k+1}=x^{s_k-1}R_k
\]

becomes:

\[
\boxed{
Q_{k+1}
=
\sum_{i=0}^{k}
x^{P_{k+1}-P_i-1}.
}
\]

Thus each affine row is a **directed phase-difference histogram** from the current endpoint to prior prefix states.

## 15.2 Formal directed-incidence lift

For every prefix pair \(i<j\), introduce formal edge:

\[
[i\to j].
\]

Physical projection:

\[
\boxed{
\pi([i\to j])
=
x^{P_j-P_i-1}
}
\]

(with anti-periodic sign included in projection).

Formal suffix row:

\[
\widetilde Q_j
=
\sum_{i<j}[i\to j].
\]

Reflection is weighted edge reversal:

\[
\mathcal J_\xi[i\to j]\sim[j\to i]
\]

with exact intertwining:

\[
\boxed{
\pi\mathcal J_\xi
=
J_\xi\pi.
}
\]

## 15.3 Formal common-core transversality

Lift common interval code to:

\[
\widetilde C^\rightarrow.
\]

Reflected:

\[
\widetilde C^\leftarrow
=
\mathcal J_\xi\widetilde C^\rightarrow.
\]

At the **formal edge level**, boundary peeling is exact: forward and reflected common-core codes use incompatible exterior-directed edges once the exchanged end intervals have been removed.

Internal result:

\[
\boxed{
\widetilde C^\rightarrow
\cap
\widetilde C^\leftarrow
=
0.
}
\]

The remaining obstruction is introduced solely by the physical projection \(\pi\).

## 15.4 Exact true bulk theorem

Need prove:

\[
\boxed{
\ker\pi_\xi
\cap
\left(
\widetilde C^\rightarrow+
\widetilde C^\leftarrow
\right)
=
\{0\}.
}
\]

If this holds, physical common-core transversality follows:

\[
C\cap JC=0.
\]

This is the current bulk theorem.

Important:

- one-sided suffix injectivity is not enough;
- forward code injective + reverse code injective does **not** imply forward/reverse transversality;
- the theorem is genuinely two-sided.

## 15.5 \(L=3\) helical displacement representation

For \(L=3\), physical phase differences admit a one-to-one helical coordinate label:

\[
\boxed{
(\Delta a,\Delta t),
\qquad
\Delta a\in\mathbb Z_d,
\quad
\Delta t\in\mathbb Z_3.
}
\]

Because \(\gcd(n_0,3)=1\), the pair determines the phase-difference class uniquely.

Thus \(\pi\) is simply a **signed histogram** over these helical displacement classes.

The canonical factor word’s horizontal cumulative residue follows an exact mountain:

\[
0\to1\to2\to\cdots\to d-1
\]

through recipient \(+1\) steps, then plateaus with donor \(-1\) events:

\[
d-1\to d-2\to\cdots\to0.
\]

Therefore the remaining bulk theorem is:

\[
\boxed{
\text{no nonzero forward/reverse coefficient packet on the canonical
3-layer mountain has zero signed weight in every helical displacement bin}.
}
\]

This is the latest completed state.

---
