#!/usr/bin/env python3
"""Exact Q(eta) reciprocal-conjugate certificates for the surviving explicit
L=3 resonant six-boundary cubics F0,F1,F2, with eta^2+eta+1=0.

This repairs the reproducibility of the cubic resultant claims.  It does NOT
invent the lost K0,K1,K2 coefficient lists; those are tracked separately in
DEBT_STATUS.md.
"""
import sympy as sp
q, eta = sp.symbols('q eta')
minpoly = eta**2 + eta + 1

F1 = 2*(eta-1)*q**3 + (4*eta+2)*q**2 - (6*eta+3)*q + 3*eta+6
F0 = 2*eta*q**3 + 2*(eta+1)*q**2 - (eta+2)*q + (1-eta)
F2 = 2*q**3 - 2*eta*q**2 + (eta-1)*q - (2*eta+1)


def reduce_eta_coeff(c):
    return sp.rem(sp.Poly(sp.expand(c),eta),sp.Poly(minpoly,eta)).as_expr()


def reduce_eta(expr):
    P=sp.Poly(sp.expand(expr),q)
    out=0
    for (k,),c in P.terms():
        out += reduce_eta_coeff(c)*q**k
    return sp.expand(out)


def conjugate_eta(expr):
    # complex conjugation in Q(eta), eta-bar=eta^2=-eta-1
    return reduce_eta(sp.expand(expr.subs(eta,-eta-1)))


def reciprocal_conjugate(F):
    P=sp.Poly(sp.expand(F),q)
    d=P.degree()
    out=0
    # q^d * conjugate(F(1/q)) = sum conjugate(c_k) q^(d-k)
    for (k,),c in P.terms():
        cc=reduce_eta_coeff(sp.expand(c.subs(eta,-eta-1)))
        out += cc*q**(d-k)
    return sp.expand(out)


def resultant_reduced(F,G):
    R=sp.resultant(F,G,q)
    return sp.factor(reduce_eta_coeff(R))


def gcd_degree_over_Qeta(F,G):
    x=sp.Symbol('x')
    alpha=sp.RootOf(x**2+x+1,0)
    FF=sp.Poly(F.subs(eta,alpha),q,extension=alpha)
    GG=sp.Poly(G.subs(eta,alpha),q,extension=alpha)
    return sp.gcd(FF,GG).degree()

for name,F in [('F0',F0),('F1',F1),('F2',F2)]:
    Fs=reciprocal_conjugate(F)
    R=resultant_reduced(F,Fs)
    gd=gcd_degree_over_Qeta(F,Fs)
    print(f"{name}(q) = {sp.expand(F)}")
    print(f"{name}#(q) = {Fs}")
    print(f"Res({name},{name}#) reduced mod eta^2+eta+1 = {R}")
    print(f"gcd degree over Q(eta) = {gd}")
    assert R != 0
    assert gd == 0
    print("PASS\n")

print("RESONANT SIX-BOUNDARY CUBIC CERTIFICATES: PASS")
