# Intrinsic-Dimension No-Reset Identification of Low-Rank Quadratic Volterra Systems

*Working draft — proved results and open problems*

## Abstract

We study identification of a second-order finite-memory Volterra model
$$f(z) = b + \ell^\top z + z^\top H z, \qquad H = H^\top, \quad \operatorname{rank} H = r,$$
from consecutive sliding windows of a single scalar input trajectory, with no
reset of the memory state between measurements. The generic parameter count is
$$D_{m,r} = 1 + m + mr - \frac{r(r-1)}{2}.$$
We give an explicit deterministic experiment attaining this intrinsic sample
count for every odd prime rank $r$ and every window length $m>r$, and reduce
the general odd-rank case to two remaining lemmas. The construction reduces
recovery of $H$ to recovery of $Y=H\Omega$ for an $r$-dimensional recurrence
subspace $\Omega$, via
$$H = Y(\Omega^\top Y)^{-1}Y^\top \quad \text{on the chart } \det(\Omega^\top H\Omega)\ne0,$$
realized through an anti-periodic recurrence $T^r=-I$. We report the proved
results, the reduction of the composite-rank case to an explicit open
combinatorial problem, and a summary of the (large) space of proof strategies
that were tried and failed, since several plausible-looking reductions turned
out to be false and this shaped the final architecture.

---

## 1. Setup

Let $u_t$ be a scalar input and $z_t=(u_t,\dots,u_{t-m+1})^\top\in\mathbb R^m$ a
length-$m$ sliding window. The measured output is
$$f(z) = b + \ell^\top z + z^\top Hz.$$
The experimental constraint is that queries $z_t$ must be *consecutive
overlapping windows of a single scalar trajectory* — arbitrary active queries
in $\mathbb R^m$ are not available, and reset between measurements is not
allowed. A generic rank-$r$ symmetric matrix has $mr - r(r-1)/2$ free
parameters, so the full model has generic dimension
$$D_{m,r} = 1 + m + mr - \frac{r(r-1)}{2}. \tag{1}$$
The goal is an explicit no-reset trajectory using exactly $D_{m,r}$ outputs
that generically identifies $(b,\ell,H)$.

**A necessary caution.** A minimal serial trajectory can have a full-rank
local parameter Jacobian while still admitting globally distinct aliases —
local identifiability does not imply global identifiability here. The serial
trajectory must be engineered as an explicit global coordinate chart, not
sampled generically.

## 2. The reduction: recurrence quotients

Pick $B\in\mathbb R^{(m-r)\times m}$, set $\Omega=\ker B$ ($\dim\Omega=r$), and
let $C=B^\top(BB^\top)^{-1}$. Every window decomposes as $z=\Omega a+Cq$ with
$q=Bz$, giving
$$f(z) = \beta+\alpha^\top a+\eta^\top q + a^\top Aa+2q^\top Ga+q^\top Kq,$$
where $A=\Omega^\top H\Omega$, $G=C^\top H\Omega$, $K=C^\top HC$. The
experiment is designed so $q$ is always zero or one-hot, deliberately leaving
the off-diagonal entries of $K$ unobserved — this blind space is exactly
$(m-r)(m-r+1)/2$-dimensional, which is what makes the sample count intrinsic.
The central *observable* object is $Y=H\Omega$.

**Theorem 1 (rank-$r$ closure).** *If $\operatorname{rank}H=r$, $Y=H\Omega$ is
known, and $\det(\Omega^\top H\Omega)\ne0$, then*
$$H = Y(\Omega^\top Y)^{-1}Y^\top. \tag{2}$$

*Proof.* Nonsingularity of $\Omega^\top H\Omega$ forces the columns of
$Y=H\Omega$ to be independent and to span $\operatorname{im}H$, so
$H=YQY^\top$ for some $r\times r$ $Q$. Right-multiplying by $\Omega$ and using
symmetry of $\Omega^\top Y$ gives $Q=(\Omega^\top Y)^{-1}$. $\blacksquare$

**Status: proved.** *(Independently verified: exact match in 500 random
instances across $(m,r)=(4,1),(5,2),(6,3),(8,4),(10,6)$.)*

### Rank-one case, in full

Set $r=1$, $s=(1,\dots,1)^\top$. Drive the trajectory through $m$ copies of
$-1$, $m$ zeros, $m$ copies of $+1$; its $2m+1=D_{m,1}$ windows are
$x_0-s,\dots,x_m-s=0,x_1,\dots,x_m$ with $x_k$ the length-$k$ indicator
vector. Writing $P_k=f(x_k)$, $N_k=f(x_k-s)$, $d_k=P_k-N_k$, one gets
$$(Hs)_k = \frac{d_k-d_{k-1}}2, \tag{3}$$
so $q:=Hs$ is known exactly, and on the chart $s^\top Hs\ne0$,
$$H = \frac{qq^\top}{s^\top q}, \qquad \ell_k = P_k-P_{k-1}-H_{kk}-2\sum_{j<k}H_{kj}, \qquad b=f(0). \tag{4}$$

**Theorem 2.** *This experiment identifies $(b,\ell,H)$ from exactly
$D_{m,1}=2m+1$ outputs, on $s^\top Hs\ne0$.* **Status: proved** (verified: exact
match in 498/500 random instances; the 2 misses were off-chart).

## 3. The anti-periodic architecture

The common serial engine for all higher ranks is
$$u_{t+r}+u_t=v_t, \qquad T^r=-I,\ T^{2r}=I, \tag{5}$$
a signed cyclic recurrence. Residual impulses create the one-hot quotient
states needed for the $q$-observations above; zero-residual intervals produce
homogeneous recurrence orbits used to probe $A=\Omega^\top H\Omega$.

## 4. Odd prime rank: the complete theorem

For $r=2H\!-\!1$ odd and $c=(m-r+1)\bmod r$ with $\gcd(c,r)=1$, use boost set
$I^*=\{0,\dots,H\!-\!2,r\!-\!1\}$ and gaps $g_k=1+r\cdot\mathbf 1_{k\in I^*}$.
The proof of nonsingularity splits into a homogeneous Fourier/Laurent argument
and a 2-adic affine correction.

**Homogeneous part.** In the invariant Laurent basis
$1,z+z^{-1},\dots,z^{H-1}+z^{-(H-1)}$, the first $H-1$ surface rows triangulate
with nonzero diagonal, and the last reduces nonsingularity to
$$P_H(t):=1+\sum_{j=1}^{H-1}(-1)^j\big(t^{2j-1}+t^{2j}\big)\ne 0 \tag{6}$$
for every physical $t$ (i.e. $t^r=\pm1$). One shows $(1+t^2)P_H(t) =
1-t+(-1)^{H-1}t^r(1+t)$, which for $t^r=\pm1$ collapses to $\pm 2/(1+t^2)$ or
$\mp 2t/(1+t^2)$ — nonzero since an odd-order root of $\pm1$ can never satisfy
$t^2=-1$.

*Verified independently:* the closed form and the nonvanishing of $P_H(t)$ at
all $2r$ physical points were checked symbolically for $r=3,5,\dots,15$; both
hold without exception.

**Affine correction.** A 2-adic/Smith-normal-form argument (full mod-2 nullity
matching the determinant's 2-adic valuation, cokernel orthogonality via an
explicit mod-4 identity) shows the affine correction cannot destroy
homogeneous invertibility. This part of the argument is intricate; we mark it
**proved internally** rather than fully re-derived here (see §9).

**Theorem 3 (odd unit-phase).** *If $r$ is odd and $\gcd(m-r+1,r)=1$, the above
construction attains $D_{m,r}$ and identifies the model generically.*

A second chart ($g_k=2+r\cdot\mathbf 1_{k\text{ odd}}$) repairs the case
$m-r+1\equiv0\pmod r$ where the first chart degenerates, via a bipartite
unimodularity argument reducing to $\det B_h=\pm1$.

**Corollary 4 (odd-prime, all $m$).** *For $r$ an odd prime and every $m>r$, an
explicit no-reset trajectory attains $D_{m,r}$ and identifies the model
generically.* This follows because modulo a prime, $m-r+1$ is either a unit
(Theorem 3 applies) or zero (the second chart applies) — no third case exists.

**This is the strongest fully closed theorem in the program.**

## 5. Composite odd rank: reduction to two lemmas

For composite odd $r$, write $n=m-r$, $d=\gcd(n,r)$, $r=dL$, $n=dn_0$ with
$\gcd(n_0,L)=1$. The obstruction is *not* simply $\gcd(n+1,r)>1$ (that
diagnosis was chart-dependent and turned out to be false); the real issue is
that $T^n$ splits phase space into $d$ disconnected cycles of length $L$,
requiring a "successor-splice" construction to reconnect them into one serial
word, plus a distinguished orbit argument.

**The $2r$ chart.** Inserting a $2r$-length excursion at a distinguished
surface $R_d$ leaves all later recurrence states unchanged (since
$T^{n+2r}=T^n$) while yielding, via $z_{t+r}=-z_t$,
$$\tfrac12\big(f(z_t)-f(-z_t)\big)=\ell^\top z_t, \qquad \tfrac12\big(f(z_t)+f(-z_t)\big)-f(0)=z_t^\top Hz_t, \tag{7}$$
i.e. $r$ clean affine and $r$ clean quadratic measurements from the same $2r$
observations. **Proved**, and the identity behind it —
$Q_{k+1}-\xi^{s_k}Q_k = R_{k+1}(u)+R_{k+1}(v)-1$ for $R_{k+1}=1+x^{s_k}R_k$,
$Q_k=R_k(u)R_k(v)$ — was independently re-derived symbolically and holds
exactly.

**The $P(T)$ orbit theorem.** With $P(x)=1+x^n\sum_{j=0}^{d-1}x^{j(n+1)}$, the
Krylov orbit $[R_d,TR_d,\dots,T^{r-1}R_d]$ is nonsingular iff
$\gcd(P,x^r+1)=1$. This reduces, via a modal-pair product argument, to an
inequality $|C|\ne1$ where $C=1+a(1-q)$, $a,q$ unit complex numbers, following
from
$$|C|^2-1 = 8\sin\tfrac Q2\sin\tfrac{A+Q}2\cos\tfrac A2 \tag{8}$$
($a=e^{iA}$, $q=e^{iQ}$) together with the coprimality $\gcd(n_0,L)=1$.

*Verified independently:* identity (8) confirmed symbolically and numerically
(2000-point sweep, residual $<10^{-14}$). $\gcd(P,x^r+1)=1$ confirmed by exact
polynomial gcd across 108 $(d,n_0,L)$ triples with $d,L$ odd $\ge3$, including
the two cases that broke earlier ad hoc constructions ($r=27=9\cdot3$,
$r=33=11\cdot3$). Notably, the theorem's domain genuinely requires $d\ge3$: at
$d=1$ (i.e. $\gcd(n,r)=1$, the non-composite case) the gcd is *not* trivial —
consistent with $d=1$ falling outside this apparatus and inside the
already-solved prime/unit-phase case instead.

**Theorem 5 ($P(T)$ orbit).** *The above Krylov orbit is nonsingular.*
**Status: proved internally**, confirmed by the checks above; full symbolic
proof is in the source report §13.

**Reduction to two lemmas.** With $F^*=(F\setminus\{(0,L\!-\!1)\})\cup\{(d\!-\!1,1)\}$
the modified reference set, the remaining odd-composite theorem needs:

- **Lemma A (reference fullness):** the $H$ full quadratic orbits indexed by
  $F^*$ span the homogeneous quadratic measurement space.
- **Lemma B (donor$\to$recipient replacement):** deleting $d-1$
  donor-boundary rows and inserting $d-1$ recipient-singleton rows preserves
  rank.

Lemma A is resolved for $L=3$ in two of three sub-cases (a resonant family via
an exact $d\to7$ boundary reduction, internally exact / computer-assisted; and
the generic non-resonant sub-case, internally closed). The remaining $L=3$
sub-case reduces to a stated combinatorial conjecture (below). $L\ge5$ and
Lemma B in general remain open.

## 6. Open problems

**Problem 1 (two-sided helical collision).** For $L=3$, label physical phase
differences by $(\Delta a,\Delta t)\in\mathbb Z_d\times\mathbb Z_3$. Consider a
formal forward/reverse pair of edge-coefficient packets on the canonical
"ascend-then-descend" chronology and their common projection $\pi$ onto this
label set. Conjecture: no nonzero forward+reverse packet has zero signed
weight in every $(\Delta a,\Delta t)$ bin, i.e.
$$\ker\pi_\xi \cap (\widetilde C^\rightarrow + \widetilde C^\leftarrow) = \{0\}.$$
One-sided injectivity of each side is already established; the open content is
that a collision *between* the two sides is impossible. **Open.**

**Problem 2 (2D boundary closure).** Conditional on Problem 1, whether
$[(I+J)b_{\rm in}]$ and $[P(u)P(v)]$ span a specific 2-dimensional defect
space. **Open.**

**Problem 3 (Lemma B, general).** Whether the donor$\to$recipient row
replacement always preserves rank. A structural subtlety: the relevant
quotient space is *not* a dynamical state (the shift operator does not descend
to it — a stripped row can leak back into the boundary after transport), so
naive fixed-dimensional autonomous-state arguments fail here. **Open.**

**Problem 4 ($L\ge5$).** Whether the reference-fullness lemma extends to all
odd $L\ge5$. Extensive numerical evidence supports this; no general proof
exists, and an earlier claimed reduction to a fixed-width residual ladder was
shown to rely on an invalid pointwise-vs-global rank argument. **Open /
evidence only.**

**Master open problem.** For every odd $r$ and every $m>r$, construct an
explicit no-reset trajectory attaining exactly $D_{m,r}$ that generically
identifies the model. Closed for all odd prime $r$ (Corollary 4); open for
composite odd $r$ pending Problems 1–3.

## 7. What did *not* work (condensed)

The program went through roughly a dozen representation changes before
reaching the above architecture. The recurring lesson, stated generally: **an
experimentally natural object is often a quotient (here $H\Omega$), not the
ambient parameter**, but quotients are only safe relative to the
transformations still to come — a quotient valid for the current observations
can become invalid once later transport or reflection acts on it. Specific
dead ends, briefly:

- *Arbitrary polarization / active recovery* — needs independent control of
  $x\pm y$, incompatible with one overlapping-window trajectory.
- *Generic random minimal trajectory + full Jacobian rank* — local full rank
  coexists with global aliasing; the chart must be engineered, not sampled.
- *"$\gcd(n+1,r)>1$ is intrinsic"* — false; the obstruction is chart-dependent
  disconnected-cycle geometry, not this specific residue.
- *Universal half-cycle staircase schedule* — failed exactly at the torus
  boundaries $r=27$ ($d=9,L=3$) and $r=33$ ($d=11,L=3$), which is what forced
  the canonical successor-splice construction.
- *Ordinary quadratic finite difference $\Rightarrow$ monomial* — false; cross
  terms survive (the correct identity is Eq. 7 above, involving both channels).
- *Dense Schur-complement elimination as "the" proof* — destroys the sparse
  recurrence structure; dense inverses here are Green functions of a sparse
  law, not evidence of intrinsic density.
- *Head resonance $\Leftrightarrow$ top-block rank defect* — false by explicit
  counterexample; some sectors have all individual heads resonant while the
  tested product-sector block stays full rank.
- *Pointwise spectral rank $\Rightarrow$ global row rank* — false; spectral
  node-dependent coefficients need not correspond to a legal global row
  combination, which is what killed the general-$L$ residual-ladder claim.
- *One-sided suffix injectivity suffices* — false; forward and reverse packets
  can collide under the physical projection even when each side alone is
  injective, which is exactly the content of Problem 1 above.

(A full table of ~30 falsified routes is preserved in the source report's
negative-results section, since several looked plausible enough to be worth
recording explicitly rather than silently dropping.)

## 8. Status summary

| Result | Status |
|---|---|
| Intrinsic dimension $D_{m,r}$ | proved |
| Rank-$r$ closure (Thm 1) | **proved**, independently verified |
| Rank-one theorem (Thm 2) | **proved**, independently verified |
| Anti-periodic architecture | proved |
| Odd unit-phase theorem (Thm 3) | proved internally; homogeneous part independently verified |
| Phase-zero repair | internally closed; proof-artifact replay debt |
| Odd-prime all-$m$ theorem (Cor. 4) | **internally closed — strongest complete result** |
| $2r$ degree separation | **proved**, identity independently verified |
| $P(T)$ orbit theorem (Thm 5) | proved internally; independently verified via gcd sweep |
| $L=3$ resonant reference (one sub-case) | internal exact / computer-assisted |
| $L=3$ generic non-resonant sub-case | internally closed |
| Two-sided collision (Problem 1) | **open** |
| 2D boundary closure (Problem 2) | **open** |
| Lemma B (Problem 3) | **open** |
| $L\ge5$ (Problem 4) | evidence only, **open** |
| Universal odd-rank theorem | **open**, reduces to Problems 1–3 |

## 9. Scope note

This draft compresses a much longer internal research record; the full
2-adic Smith-normal-form derivation (§6.2 of the source), the complete
resonant-$L{=}3$ boundary algebra (§15), the reflection/interval-code surgery
(§18–19), and the full negative-results table are omitted here for length and
should be consulted in the source report before any external submission. Independent
computational verification of every claim reconstructable from this document
alone is reported separately (`VERIFICATION_REPORT.md`); it confirms all
checkable identities and flags exactly the reproducibility gaps the source
already anticipated in its own §27.
