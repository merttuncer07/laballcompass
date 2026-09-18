# Resonant L=3 fixed-state reproducibility repair

## Scope

This note repairs the remaining saved-artifact debt for the internally exact characteristic-zero theorem in the resonant branch

\[
L=3,\qquad n=d,\qquad r=3d,\qquad d=2e+1.
\]

The historical handoff preserved the theorem structure and the degrees

\[
\deg K_1=12,\qquad \deg K_0=13,\qquad \deg K_2=13,
\]

with reciprocal-conjugate certificates

\[
\gcd(K_i,K_i^\sharp)=1,
\]

but not the coefficient lists or the exact saved certificate script.

The repair below reconstructs them from the physical no-reset experiment itself.

---

## 1. Physical-to-semi-regular bridge

Let \(\Delta\) denote the resonant primitive-idempotent row, scaled in coefficient coordinates as

\[
\Delta_k=(-1)^kq^{d-1-k},\qquad 0\le k<d.
\]

The physical resonant \(u\)-head at the distinguished \(P\)-state satisfies

\[
P_u(Z)=\sum_{k=1}^{d-1}(-1)^{k+1}q^{-k}Z^k.
\]

Therefore exactly

\[
\boxed{q^{d-1}P_u=q^{d-1}\mathbf 1-\Delta.}
\]

Since \(\Delta\) is the primitive idempotent supported at \(Z=-q\), multiplication by any Laurent polynomial \(g\) obeys

\[
\Delta g=g(-q)\Delta.
\]

Consequently the physical quadratic distinguished row obeys

\[
\boxed{
q^{d-1}P_uP_v
=q^{d-1}P_v-P_v(-q)\Delta.
}
\]

This reconstructs the historical statement that the physical \(P\)-row is row-equivalent modulo \(\Delta\) to the one-channel \(P_v\)-row.

At the center, let \(H_{\rm phys}=U_e+V_e-1\) and define the semi-regular center by

\[
H:=V_e.
\]

The physical resonant head gives

\[
\boxed{q^{d-1}(U_e-1)=-\Delta,}
\]

hence

\[
\boxed{
q^{d-1}H_{\rm phys}=q^{d-1}H-\Delta.
}
\]

For the lower closure row define

\[
\bar U_0=1+2\sum_{k=1}^{e}q^kZ^{-k},
\qquad
C_0=1+\bar U_0+\eta V_0.
\]

Direct reduction using the physical relation \(q^d=\rho\) gives

\[
\boxed{
q^{d-1}(U_0-\bar U_0)=(-1)^{e+1}\Delta,
}
\]

while the \(v\)-channel is unchanged. Thus

\[
\boxed{
q^{d-1}I_{0,\rm phys}
=q^{d-1}C_0+(-1)^{e+1}\Delta.
}
\]

These are triangular row operations after \(\Delta\) is included. Therefore the physical seven-row boundary determinant and the normalized seven-row determinant have the same zero set on physical nonzero \(q\)-nodes, up to harmless monomial/scalar factors.

---

## 2. Normalized boundary system from physical states

No guessed historical closure formula is required.

The normalized system is reconstructed directly from the physical state generator:

\[
H=V_e,
\qquad
B_e=V_{e-1}-V_e,
\]

\[
D_j=2q^{j+1}Z^{-j-1}+B_eZ^j,
\qquad j=0,1,2,
\]

with the actual physical one-channel row \(P_v\) and

\[
C_0=1+\bar U_0+\eta V_0.
\]

After the proved interior elimination, the seven surviving Laurent coordinates are exactly

\[
\boxed{
Z,\ Z^2,\ Z^3,\ Z^e,\ Z^{d-3},\ Z^{d-2},\ Z^{d-1}.
}
\]

---

## 3. Fixed-state period-six reduction

Write

\[
t=q^e,\qquad qt^2=\rho.
\]

For fixed \(e\bmod6\), compare \(d\), \(d+12\), and \(d+24\). Exact symbolic computation gives:

1. the six non-\(\Delta\) boundary rows have the same annihilator cofactors;
2. the \(t\)-independent part of the delta pairing is identical;
3. the changing coefficient obeys
   \[
   B_{e+6}-B_e=q^{e+1}H(q),
   \]
   with the same fixed polynomial \(H\);
4. the next step satisfies
   \[
   B_{e+12}-B_{e+6}=q^{e+7}H(q).
   \]

Thus the entire growing tail is a geometric series in \(q^6\). After summation and use of \(qt^2=\rho\), the zero condition is a fixed-degree polynomial \(G_i(q)\), independent of the size of \(d\) inside that residue class.

This is the saved handoff's period-2 / period-3 \(\operatorname{lcm}(2,3)=6\) mechanism in an executable exact form.

---

## 4. Exact factorization

Let \(\eta^2+\eta+1=0\). Define the common geometric factor

\[
\mathcal G(q)
=(q-1)^2(q+1)^2(q+\eta)^2(q+\eta^2)^2(q-\eta^2)^2.
\]

The reconstructed fixed-state obstructions factor as follows.

### Branch \(d\equiv1\pmod3\)

\[
\boxed{
G_1(q)\doteq (q-\eta)\,\mathcal G(q)\,K_1(q),
\qquad \deg K_1=12.
}
\]

### Branch \(d\equiv0\pmod3\)

\[
\boxed{
G_0(q)\doteq \mathcal G(q)\,K_0(q),
\qquad \deg K_0=13.
}
\]

### Branch \(d\equiv2\pmod3\)

\[
\boxed{
G_2(q)\doteq \mathcal G(q)\,K_2(q),
\qquad \deg K_2=13.
}
\]

In particular \(\mathcal G\) contains the historical displayed core

\[
(q-1)^2(q-\eta^2)^2,
\]

while the additional factors \((q+1)^2(q+\eta)^2(q+\eta^2)^2\) are nonphysical geometric factors and may be removed before presenting the historical \(G_2\) normalization.

---

## 5. Physical-node classification

Physical nodes satisfy

\[
q^d=\rho,
\qquad
\rho=
\begin{cases}
\eta^2,&d\equiv0\pmod3,\\
\eta,&d\equiv1\pmod3,\\
1,&d\equiv2\pmod3.
\end{cases}
\]

For odd \(d\), the geometric roots

\[
-1,\ -\eta,\ -\eta^2,\ \eta^2
\]

never satisfy the corresponding physical relation in any branch.

The two geometric roots that can be physical are exactly the ones identified in the historical handoff:

- \(q=\eta\) in the \(d\equiv1\) branch;
- \(q=1\) in the \(d\equiv2\) branch.

They are removable artifacts of the fixed-state geometric elimination, so they must be evaluated in the original finite physical determinant. Exact evaluations in both \(e\bmod6\) classes are nonzero. Representative exact outputs include

\[
d=7:\quad G_{\rm phys}(\eta)=1332+396\eta\ne0,
\]

\[
d=13:\quad G_{\rm phys}(\eta)=-468-2664\eta\ne0,
\]

and

\[
d=11:\quad G_{\rm phys}(1)=144,
\]

\[
d=17:\quad G_{\rm phys}(1)=-144,
\]

\[
d=23:\quad G_{\rm phys}(1)=144.
\]

---

## 6. Reciprocal-conjugate certificates

For

\[
K(q)=A(q)+\eta B(q),
\]

define

\[
K^\sharp(q)=q^{\deg K}\,\overline{K(1/q)},
\qquad \overline\eta=\eta^2.
\]

The exact script reconstructs the three residual factors and obtains

\[
\boxed{
\gcd(K_0,K_0^\sharp)=
\gcd(K_1,K_1^\sharp)=
\gcd(K_2,K_2^\sharp)=1.
}
\]

Therefore none of the residual factors has a unit-circle zero.

The coefficient lists are emitted verbatim by `VOLTERRA_RESONANT_FIXED_STATE_CERT.py`.

---

## 7. Reproducibility verdict

The previously missing resonant certificate is now reproducible from:

1. the physical scalar no-reset schedule;
2. exact integer recurrence states;
3. exact modal evaluation over \(\mathbb Q(\eta)\);
4. the proved \(d\to7\) interior elimination;
5. the explicit physical-to-normalized \(\Delta\)-bridge;
6. the exact period-six fixed-state recurrence;
7. exact factorization and Euclidean gcd computations.

No numerical fitting and no floating-point root test is used.

**Status: reproducibility debt repaired for the resonant `L=3,n=d` certificate layer.**
