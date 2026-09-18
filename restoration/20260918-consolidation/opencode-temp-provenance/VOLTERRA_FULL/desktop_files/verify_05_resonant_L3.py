"""
Certificate 7: resonant L=3, n=d rescue theorem (Section 15.4), the F0/F1/F2 part.

The report gives explicit degree-3 polynomials in q, with eta a primitive cube
root of unity (eta^2+eta+1=0, eta != 1):

  F1(q) = 2(eta-1) q^3 + (4 eta+2) q^2 - (6 eta+3) q + 3 eta + 6      [d = 1 mod 3]
  F0(q) = 2 eta q^3     + 2(eta+1) q^2 - (eta+2) q     + (1-eta)      [d = 0 mod 3]
  F2(q) = 2 q^3 - 2 eta q^2 + (eta-1) q - (2 eta+1)                  [d = 2 mod 3]

and asserts each has a nonzero "reciprocal-conjugate resultant".

IMPORTANT CAVEAT: the report does not define "reciprocal-conjugate" precisely
within this consolidated document (that convention lives in the un-supplied
internal sources S1/S2). We use the standard construction from self-inversive
polynomial theory: for F of degree n with coefficients depending on eta,

    F^sharp(q) = q^n * conj_eta(F)(1/q)

where conj_eta replaces eta -> eta^2 = conjugate(eta) (eta lies on the unit
circle, eta^2 is its complex conjugate). We then test whether Res(F, F^sharp)
is nonzero. This interpretation is INFERRED, not confirmed against the
original source, and is flagged as such in the accompanying report.

We also independently check the more basic (unambiguous) claims: F0, F1, F2
are themselves algebraically as stated and are non-identically-zero, and have
no roots on the unit circle |q|=1 in common with their conjugate-reciprocal
(the numerically meaningful content of "resultant nonzero").
"""
import sympy as sp

q, eta = sp.symbols('q eta')
eta_num = sp.exp(2*sp.pi*sp.I/3)  # primitive cube root of unity
eta_conj_num = sp.exp(-2*sp.pi*sp.I/3)  # = eta^2

F1 = 2*(eta-1)*q**3 + (4*eta+2)*q**2 - (6*eta+3)*q + 3*eta + 6
F0 = 2*eta*q**3 + 2*(eta+1)*q**2 - (eta+2)*q + (1-eta)
F2 = 2*q**3 - 2*eta*q**2 + (eta-1)*q - (2*eta+1)

def reciprocal_conjugate(F, var, eta_sym, eta_conj_val):
    n = sp.degree(F, var)
    Fc = F.subs(eta_sym, eta_conj_val)
    Fsharp = sp.expand(var**n * Fc.subs(var, 1/var))
    return Fsharp

def resultant_nonzero_numeric(F, name):
    Fq = F.subs(eta, eta_num)
    Fsharp = reciprocal_conjugate(Fq, q, eta, eta_conj_num)  # already substituted eta above; conj step below
    # Build F^sharp directly at the numeric eta: conj coefficients then reciprocal.
    Fq_over_eta = F  # keep symbolic in eta for coefficient conjugation
    n = sp.degree(Fq_over_eta, q)
    F_conjcoef = Fq_over_eta.subs(eta, eta_conj_num)
    Fsharp_expr = sp.expand(q**n * F_conjcoef.subs(q, 1/q))
    Fsharp_expr = sp.nsimplify(sp.expand(Fsharp_expr))
    res = sp.resultant(sp.Poly(Fq, q), sp.Poly(Fsharp_expr, q))
    res_val = complex(sp.N(res, 25))
    print(f"{name}: Res(F, F^sharp) = {res_val}   |Res| = {abs(res_val):.6g}   nonzero: {abs(res_val) > 1e-8}")
    return res_val

print("=== Reciprocal-conjugate resultants (inferred construction) ===")
resultant_nonzero_numeric(F1, "F1 (d=1 mod 3)")
resultant_nonzero_numeric(F0, "F0 (d=0 mod 3)")
resultant_nonzero_numeric(F2, "F2 (d=2 mod 3)")

print("\n=== Unit-circle common-root check (equivalent to resultant=0) ===")
for name, F in [("F1", F1), ("F0", F0), ("F2", F2)]:
    Fq = sp.expand(F.subs(eta, eta_num))
    roots = sp.Poly(Fq, q).nroots(n=30)
    on_circle = [complex(r) for r in roots if abs(abs(complex(r)) - 1) < 1e-6]
    print(f"{name}: roots = {[complex(r) for r in roots]}")
    print(f"   roots on unit circle: {on_circle}")

print("\n=== Sanity: are F0, F1, F2 identically zero for any eta with eta^3=1, eta!=1? ===")
for name, F in [("F1", F1), ("F0", F0), ("F2", F2)]:
    is_zero = sp.expand(F.subs(eta, eta_num)) == 0
    print(f"{name} identically zero at eta=primitive cube root: {is_zero}")
