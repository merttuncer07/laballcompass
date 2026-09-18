"""
Certificate 6: gcd(P, x^r+1) = 1 (Section 13, distinguished P(T) orbit theorem)

  P(x) = 1 + x^n * sum_{j=0}^{d-1} x^{j(n+1)},   r = dL,  n = d*n0,  gcd(n0, L) = 1

We check this by exact polynomial gcd over Q (equivalently over C, since both
polynomials have rational integer coefficients) for a wide sweep of odd
(d, L, n0) triples satisfying the report's hypotheses (d odd, L odd,
gcd(n0, L) = 1), including the hard case explicitly flagged as a past failure
point in the report (r = 27 = 9*3 and r = 33 = 11*3).
"""
import sympy as sp
from math import gcd

x = sp.symbols('x')

def P_poly(d, n0, L):
    n = d * n0
    r = d * L
    expr = 1 + x**n * sum(x**(j*(n+1)) for j in range(d))
    return sp.expand(expr), r

def check(d, n0, L):
    if gcd(n0, L) != 1:
        return None
    P, r = P_poly(d, n0, L)
    target = x**r + 1
    g = sp.gcd(sp.Poly(P, x), sp.Poly(target, x))
    return r, g.as_expr()

print("=== gcd(P, x^r+1) sweep, d and L odd, gcd(n0,L)=1 ===")
failures = []
tested = 0
for d in [1, 3, 5, 7, 9, 11]:
    for L in [1, 3, 5, 7]:
        if d % 2 == 0 or L % 2 == 0:
            continue
        for n0 in range(1, 6):
            res = check(d, n0, L)
            if res is None:
                continue
            r, g = res
            tested += 1
            is_unit = (sp.Poly(g, x).degree() == 0)
            if not is_unit:
                failures.append((d, n0, L, r, g))

print(f"Tested {tested} (d,n0,L) triples.")
if failures:
    print("FAILURES (gcd not a unit):")
    for f in failures:
        print("  ", f)
else:
    print("All instances: gcd(P, x^r+1) is a nonzero constant (degree 0) -> gcd = 1 confirmed.")

print("\n=== Explicit check of the two historically hard cases flagged in the report ===")
for (d, L) in [(9, 3), (11, 3)]:
    for n0 in range(1, 4):
        if gcd(n0, L) != 1:
            continue
        r, g = check(d, n0, L)
        print(f"d={d}, L={L}, n0={n0}, r={r}: gcd = {g}  (unit: {sp.Poly(g,x).degree()==0})")
