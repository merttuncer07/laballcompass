"""
Certificate 3: nonvanishing of P_H(t) for all physical t with t^r = +-1, r odd
(report Section 6.1, Theorem "odd unit-phase theorem" homogeneous part).

The report defines, for r = 2H-1:
   a_*(q)   = sum_{j=0}^{H-2} q^j + q^{H-1} sum_{j=0}^{H-1} (-q)^j
   P_H(t)   = coefficient of a_*(tz)a_*(t/z) in the top invariant Laurent direction
            = 1 + sum_{j=1}^{H-1} (-1)^j (t^{2j-1} + t^{2j})
and derives the closed form
   (1+t^2) P_H(t) = 1 - t + (-1)^{H-1} t^r (1+t).

We check (a) the closed form is algebraically correct (symbolic identity),
and (b) P_H(t) != 0 at every t with t^r = 1 or t^r = -1, for a range of odd r.
"""
import sympy as sp

t = sp.symbols('t')

def PH_series(H):
    expr = 1
    for j in range(1, H):
        expr += (-1)**j * (t**(2*j-1) + t**(2*j))
    return sp.expand(expr)

def PH_closed_lhs_rhs(H, r):
    PH = PH_series(H)
    lhs = sp.expand((1 + t**2) * PH)
    rhs = sp.expand(1 - t + (-1)**(H-1) * t**r * (1 + t))
    return lhs, rhs

print("=== Closed-form identity (1+t^2) P_H(t) = 1 - t + (-1)^(H-1) t^r (1+t) ===")
for H in range(2, 9):
    r = 2*H - 1
    lhs, rhs = PH_closed_lhs_rhs(H, r)
    diff = sp.simplify(lhs - rhs)
    print(f"H={H}, r={r}: identity holds = {diff == 0}")

print("\n=== Nonvanishing of P_H(t) at all physical t (t^r = +-1), r odd ===")
for H in range(2, 9):
    r = 2*H - 1
    PH = PH_series(H)
    bad = []
    # t^r = 1 -> t = primitive r-th roots of unity (all r of them, including 1)
    for k in range(r):
        tv = sp.exp(2*sp.pi*sp.I*k/r)
        val = sp.nsimplify(sp.simplify(PH.subs(t, tv)), rational=False)
        val_num = complex(sp.N(val, 20))
        if abs(val_num) < 1e-9:
            bad.append(('t^r=1', k, val_num))
    # t^r = -1 -> t = exp(i pi (2k+1)/r)
    for k in range(r):
        tv = sp.exp(sp.I*sp.pi*(2*k+1)/r)
        val = sp.simplify(PH.subs(t, tv))
        val_num = complex(sp.N(val, 20))
        if abs(val_num) < 1e-9:
            bad.append(('t^r=-1', k, val_num))
    status = "OK, never zero" if not bad else f"FAILS at {bad}"
    print(f"H={H}, r={r}: {status}  ({2*r} physical points checked)")
