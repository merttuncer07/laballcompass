# Independent Verification Report
### ALAN Volterra Programme — Reproducibility & Certificate Debt (§27)

This note reports the results of independently reconstructing and checking, by
direct symbolic/numeric computation, every claim in the report that is stated
with enough explicit detail to be reconstructed from the document alone. Five
scripts are provided (`verify_01`–`verify_05`); all use only Python + SymPy/NumPy
and can be re-run as standalone certificates.

**Bottom line: every claim that could be reconstructed from the report's own
formulas checked out.** Nothing here reveals a computational error in the
proved/internally-proved theorems. The genuine reproducibility gaps the report
already flags in §27 (phase-zero $B_h$, the $K_0,K_1,K_2$ certificates) turn
out to be gaps for a structural reason: the report states *properties* of
those objects but does not give the underlying matrices/polynomials explicitly
enough to rebuild them from this document alone. That is a real debt, not one
I can close by inference — closing it needs the internal sources S1/S2/S5/S6
listed in the bibliography, which were not provided.

---

## 1. What was verified, and how

| # | Claim | Report location | Method | Result |
|---|---|---|---|---|
| 1 | Rank-one serial theorem: $H=\frac{qq^\top}{s^\top q}$, $q=Hs$ recovered via finite differences, then $\ell$ via the telescoping formula | §3, Thm 3.1 | Simulated 100 random rank-1 $(H,\ell,b)$ instances per $m\in\{1,2,3,5,8\}$, ran the exact experiment, compared reconstruction to ground truth | **Exact match** in all on-chart instances (2 skips at $m=8$ were near-singular chart, not errors) |
| 2 | Generic rank-$r$ closure: $H=Y(\Omega^\top Y)^{-1}Y^\top$ | §4, Thm 4.1 | 100 random instances per $(m,r)\in\{(4,1),(5,2),(6,3),(8,4),(10,6)\}$ | **Exact match**, all instances |
| 3 | Closed form $(1+t^2)P_H(t)=1-t+(-1)^{H-1}t^r(1+t)$ and nonvanishing of $P_H(t)$ at every physical $t$ with $t^r=\pm1$ | §6.1 | Symbolic identity check + exact evaluation at all $2r$ roots, for $r=3,5,\dots,15$ | Closed form **holds identically**; $P_H(t)$ **never zero** at any tested physical point |
| 4 | Quadratic-to-affine identity $Q_{k+1}-\xi^{s_k}Q_k = R_{k+1}(u)+R_{k+1}(v)-1$ | §11 | Symbolic expansion (SymPy) | **Holds identically** |
| 5 | Trig identity $|C|^2-1 = 8\sin\frac Q2\sin\frac{A+Q}2\cos\frac A2$ | §13, eq. 50 | Symbolic simplification + 2000-point numeric sweep | **Holds identically** (max numeric residual $5\times10^{-15}$, i.e. floating-point noise) |
| 6 | $\gcd(P,x^r+1)=1$ for the distinguished $P(T)$ orbit, $P(x)=1+x^n\sum_{j=0}^{d-1}x^{j(n+1)}$ | §13, Thm 13.1 | Exact polynomial `gcd` over $\mathbb Q$ for 108 $(d,n_0,L)$ triples with $d,L$ odd $\ge3$, $\gcd(n_0,L)=1$, including the historically hard cases $r=27=9\cdot3$ and $r=33=11\cdot3$ flagged in §8 | **$\gcd=1$ in every instance tested**, including both hard cases |
| 7 | Reciprocal-conjugate resultants of $F_0,F_1,F_2$ nonzero | §15.4 | Resultant of $F$ against its reciprocal-conjugate (see caveat below), numeric at $\eta=e^{2\pi i/3}$; cross-checked by confirming no common root lies on $|q|=1$ | **All three resultants nonzero** ($|{\rm Res}|=23004,\,780,\,192$ respectively) under the stated construction |

## 2. An interesting boundary finding (item 6)

While sweeping item 6, every triple with $d=1$ produced a **nontrivial** gcd
($x+1$). On inspection this is not a counterexample: $d=\gcd(n,r)=1$ means the
base motion $T^n$ already acts as a single full-length cycle, i.e. exactly the
*non*-composite regime the report says is handled instead by the earlier
odd unit-phase / phase-zero theorems (§6–§7), not by the $P(T)$-orbit
apparatus, which is built specifically for genuine factor-splitting $d>1$.
Once restricted to $d\ge3$ — the actual domain of Theorem 13.1 — all 108
tested instances give $\gcd=1$ with no exceptions. Worth noting explicitly in
any future write-up of Theorem 13.1, since the hypothesis "$d,L$ odd" alone
doesn't rule out $d=1$ on its face.

## 3. Caveat on item 7

The report uses the shorthand "reciprocal-conjugate resultant" and $K_i^\sharp$
notation without defining the operation inside this document. I used the
standard self-inversive-polynomial construction — $F^\sharp(q) = q^{\deg F}\cdot
\overline{F}(1/q)$ with $\eta\mapsto\bar\eta=\eta^2$ — which is the natural
candidate given $\eta$ lies on the unit circle and the surrounding context is a
unit-circle nonvanishing argument (parallel to the $t^2=-1$ obstruction in
§6.1). The nonvanishing held under this construction, but **this is an
inference about notation, not a confirmation that it matches the internal
source's actual definition.** Flagging this explicitly rather than presenting
it as a closed match.

## 4. What could *not* be independently reconstructed, and why

These are not failures of computation — they are places where the report
states a *property* of an object (its rank, its Smith form, its degree) without
giving enough of the object's actual construction to rebuild it from this
document alone:

- **Phase-zero $B_h$ unimodularity** (§7). The report gives the wrap equations
  $z_p=(2p+1)z_0$, $w_p=2(p+1)z_0$ and asserts the final dense row reduces to
  $-z_0=0$, which *is* the proof sketch, but doesn't specify $B_h$'s full
  entry-by-entry construction (how the bipartite orbit rows are indexed and
  populated for general $h$) needed to build the matrix independently and
  recompute its determinant as a check. Needs source S5/S6.
- **$\operatorname{SNF}(M_r^{(\nu)})$** (§7, eq. 32) and the general **2-adic affine
  correction matrix $P$** (§6.2). Both are stated as results of an indexing
  scheme (boosted surfaces, anchor states, cross-term quadratics $C_j$) that is
  described qualitatively but not pinned down as an explicit algorithm for
  general $r$. Reconstructing "the" matrix would require guessing conventions
  the report doesn't fix, so any agreement or disagreement I got would be
  meaningless. Needs source S4.
- **$K_0,K_1,K_2$** (§15.4). The report gives their degrees (13, 12, 13) and a
  gcd-coprimality property but not the polynomials themselves — they come from
  eliminating the six-boundary determinant against $F_0,F_1,F_2$, which itself
  needs matrix data from §15.1–15.3 (the $\tau_a$, $Z$, $\Lambda$ machinery)
  that isn't fully instantiated numerically in this document. Needs source S2.

These three are exactly the items §27 already flags as reproducibility debt —
independent reconstruction confirms that the debt is real and specifically
localized to missing explicit constructions, not to any inconsistency visible
from this report alone.

## 5. Files

- `verify_01_linear_algebra.py` — rank-one theorem, rank-$r$ closure theorem
- `verify_02_odd_unit_phase.py` — $P_H(t)$ closed form and nonvanishing
- `verify_03_quad_to_affine_and_trig.py` — quadratic-to-affine identity, eq. 50 trig identity
- `verify_04_PT_orbit_gcd.py` — $\gcd(P,x^r+1)=1$ sweep, including the $r=27,33$ hard cases
- `verify_05_resonant_L3.py` — $F_0,F_1,F_2$ resultant nonvanishing (with the notation caveat above)

Run any of them with `python3 verify_0N_*.py`; each is self-contained.
